import random
from datetime import datetime
from typing import Union, Optional

from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert

from app.base.base_accessor import BaseAccessor
from app.game.models import UserModel, User, GameModel, UsersOfGameModel, BrokerageAccountModel, SecuritiesModel, \
    SecuritiesForGameModel, Securities, VKProfile, GameWithOptions, BrokerageAccount, SecuritiesForGame, EventModel, \
    Event, Game, WinnerModel, GameWithWinner, Winner
from app.game.text import NO_MONEY, BOUGHT, ALREADY_END_ROUND, USER_END_ROUND, GAME_ENDED, BIG_COUNT, \
    DONT_HAVE_SECURITIES, CELLED
from app.store.database.gino import db
from app.store.vk_api.dataclasses import Update
from app.web.app import Application


class GameAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        await app.database.connect()

    async def prepare_to_start_game(self, update: Update, profiles: list[VKProfile]) -> list[Securities]:
        users = await self.create_users(profiles)
        return await self.create_game(update, users)

    @staticmethod
    async def create_users(profiles: list[VKProfile]) -> list[User]:
        await insert(UserModel).values(
            [
                {
                    'vk_id': profile.id,
                    'fio': f'{profile.first_name} {profile.last_name}',
                    'create_at': datetime.now()
                }
                for profile in profiles
            ]
        ).on_conflict_do_nothing(index_elements=['vk_id']).gino.all()

        res = await UserModel.query.gino.all()

        return [User(**user.to_dict()) for user in res]

    async def create_game(self, update: Update, users: list[User]) -> list[Securities]:
        finished = {}
        for user in users:
            finished[str(user.vk_id)] = False

        async with db.transaction() as _:
            game = await GameModel.create(
                created_at=datetime.now(),
                chat_id=update.object.peer_id,
                round=1,
                users_finished_round=finished,
                state='GOING'
            )

            await self.create_users_of_game(game.id, users)
            await self.create_brokerage_accounts_for_users(game.id, users)
            securities = await self.create_securities_for_game(game.id)

            return securities

    @staticmethod
    async def create_users_of_game(game_id: int, users: list[User]):
        await UsersOfGameModel.insert().gino.all(
            [
                {
                    'game_id': game_id,
                    'user_id': user.id
                }
                for user in users
            ]
        )

    @staticmethod
    async def create_brokerage_accounts_for_users(game_id: int, users: list[User]):
        await BrokerageAccountModel.insert().gino.all(
            [
                {
                    'game_id': game_id,
                    'user_id': user.id,
                    'money': 1000,
                    'securities': {}
                }
                for user in users
            ]
        )

    async def create_securities_for_game(self, game_id: int) -> list[Securities]:
        securities = await self.get_securities()

        await SecuritiesForGameModel.insert().gino.all(
            [
                {
                    'description': s.description,
                    'cost': s.cost,
                    'code': s.code,
                    'game_id': game_id
                }
                for s in securities
            ]
        )

        return securities

    @staticmethod
    async def get_going_game(chat_id: int) -> GameModel:
        game = await GameModel.query.where(
            and_(GameModel.chat_id == chat_id, GameModel.state == 'GOING')
        ).gino.first()
        return game

    @staticmethod
    async def get_securities() -> list[Securities]:
        res = await SecuritiesModel.query.gino.all()

        return [
            s.as_dc()
            for s in res
        ]

    @staticmethod
    def get_game_query():
        return GameModel.outerjoin(
            UsersOfGameModel, GameModel.id == UsersOfGameModel.game_id
        ).outerjoin(
            UserModel, UsersOfGameModel.user_id == UserModel.id
        ).outerjoin(
            SecuritiesForGameModel, GameModel.id == SecuritiesForGameModel.game_id
        ).select()

    async def get_game_with_options(self, chat_id: int, code: Optional[str] = None) -> Union[GameWithOptions, list]:
        res = (await self.get_game_query().where(
            and_(GameModel.chat_id == chat_id, GameModel.state == 'GOING')
        ).gino.load(
            GameModel.distinct(GameModel.id).load(
                users=UserModel,
                securities=SecuritiesForGameModel
            )
        ).all())
        # TODO: нихрена не работает в питоне, зато работает в бд
        if not res:
            return []

        res = res[0]
        return GameWithOptions(
            id=res.id,
            chat_id=res.chat_id,
            created_at=res.created_at,
            round=res.round,
            users_finished_round=res.users_finished_round,
            state=res.state,
            users=[
                User(**user.to_dict())
                for user in res.users
            ],
            securities=[
                SecuritiesForGameModel(**s.to_dict())
                for s in res.securities if code is None or s.code == code
            ]
        )

    @staticmethod
    async def buy_securities(vk_id: int, securities: SecuritiesForGameModel, count: str) -> str:
        brok_acc_model = (
            await BrokerageAccountModel.outerjoin(
                UserModel, UserModel.id == BrokerageAccountModel.user_id
            ).select().where(
                and_(UserModel.vk_id == vk_id, BrokerageAccountModel.game_id == securities.game_id)
            ).gino.load(
                BrokerageAccountModel.distinct(BrokerageAccountModel.id).load(user=UserModel)
            ).all()
        )[0]
        brok_acc = BrokerageAccount(**brok_acc_model.to_dict())

        cost = round(securities.cost * int(count), 2)
        money = brok_acc.money - cost
        if money < 0:
            return NO_MONEY + f'У вас в кошельке {brok_acc.money}'

        if brok_acc.securities.get(securities.code) is not None:
            brok_acc.securities[securities.code] += int(count)
        else:
            brok_acc.securities.update(
                {
                    securities.code: int(count),
                }
            )

        securities_json = brok_acc.securities

        await brok_acc_model.update(securities=securities_json, money=money).apply()
        return BOUGHT + f'У вас в кошельке осталось {money}'

    @staticmethod
    async def cell_securities(vk_id: int, securities: SecuritiesForGameModel, count: str) -> str:
        brok_acc_model = (
            await BrokerageAccountModel.outerjoin(
                UserModel, UserModel.id == BrokerageAccountModel.user_id
            ).select().where(
                and_(UserModel.vk_id == vk_id, BrokerageAccountModel.game_id == securities.game_id)
            ).gino.load(
                BrokerageAccountModel.distinct(BrokerageAccountModel.id).load(user=UserModel)
            ).all()
        )[0]
        brok_acc = BrokerageAccount(**brok_acc_model.to_dict())

        if brok_acc.securities.get(securities.code) is None:
            return DONT_HAVE_SECURITIES

        if brok_acc.securities[securities.code] < int(count):
            return BIG_COUNT + str(brok_acc.securities[securities.code])

        cost = round(securities.cost * int(count), 2)
        money = brok_acc.money + cost

        brok_acc.securities[securities.code] -= int(count)

        securities_json = brok_acc.securities

        await brok_acc_model.update(securities=securities_json, money=money).apply()
        return CELLED + f'У вас в кошельке {money}. Осталось {securities.code}: {securities_json[securities.code]}'

    @staticmethod
    async def get_information_from_securities(
            securities: list[SecuritiesForGame],
            securities_models: list[SecuritiesForGameModel],
            events: list[Event]
    ) -> str:
        information = ''
        for s, sm in zip(securities, securities_models):
            event = random.choice(events)
            old_cost = s.cost
            s.cost = round(s.cost * event.diff, 2)
            await sm.update(cost=s.cost).apply()
            information += f'{event.text} Акции {s.code} изменились на {event.diff}. Старая цена {old_cost}.' \
                           f' Новая цена {s.cost}. '

        return information

    async def get_events(self, game_id: int) -> str:
        event_models = await EventModel.query.gino.all()
        events = [
            Event(**event.to_dict())
            for event in event_models
        ]

        securities_models = await SecuritiesForGameModel.query.where(
            SecuritiesForGameModel.game_id == game_id
        ).gino.all()
        securities = [
            SecuritiesForGame(**s.to_dict())
            for s in securities_models
        ]

        return await self.get_information_from_securities(securities, securities_models, events)

    async def end_game(self, game: GameModel) -> str:
        information = GAME_ENDED + await self.get_winner(game.chat_id)
        await game.update(state='ENDED').apply()

        return information

    async def get_winner(self, chat_id: int) -> str:
        game = await self.get_game_with_options(chat_id)
        costs_of_securities = {}
        for s in game.securities:
            costs_of_securities[s.code] = s.cost

        wallets = []
        for user in game.users:
            broc_acc = BrokerageAccount(
                **(
                    await BrokerageAccountModel.query.where(
                        and_(BrokerageAccountModel.user_id == user.id, BrokerageAccountModel.game_id == game.id)
                    ).gino.first()
                ).to_dict()
            )
            money = broc_acc.money
            self.logger.info(costs_of_securities)

            for key in broc_acc.securities:
                money += broc_acc.securities[key] * costs_of_securities[key]

            wallets.append({'fio': user.fio, 'vk_id': user.vk_id, 'money': money, 'win_count': user.win_count})
        wallet = max(wallets, key=lambda w: w['money'])
        await WinnerModel.create(vk_id=wallet['vk_id'], game_id=game.id)
        await UserModel.update.where(UserModel.vk_id == wallet['vk_id']).values({
            'win_count': wallet['win_count'] + 1
        }).gino.all()
        return f'Победитель {wallet["fio"]}. Цена его кошелька {wallet["money"]}'

    async def end_round(self, vk_id: str, game_model: GameModel) -> str:
        game = Game(**game_model.to_dict())

        if game.users_finished_round[vk_id]:
            return ALREADY_END_ROUND

        game.users_finished_round[vk_id] = True
        async with db.transaction() as _:
            await game_model.update(users_finished_round=game.users_finished_round).apply()
            if not all(finished for finished in game.users_finished_round.values()):
                return USER_END_ROUND

            for user_id in game.users_finished_round:
                game.users_finished_round[user_id] = False
            game.round += 1
            await game_model.update(users_finished_round=game.users_finished_round, round=game.round).apply()

            if game.round == 11:
                return await self.end_game(game_model)

            return await self.get_events(game.id) + 'Начинается новый раунд.'

    @staticmethod
    async def get_games_with_winners(limit: int, page: int) -> list[GameWithWinner]:
        games = await GameModel.outerjoin(
            WinnerModel, WinnerModel.game_id == GameModel.id
        ).select().order_by(GameModel.id).limit(limit).offset(page * limit - limit).gino.load(
            GameModel.distinct(GameModel.id).load(winner=WinnerModel)).all()

        return [
            GameWithWinner(**game.to_dict(),
                           winner=Winner(game.winner.vk_id) if game.winner else None
                           )
            for game in games
        ]

    @staticmethod
    async def get_winner_by_game_id(game_id: int) -> Optional[User]:
        user = await UserModel.outerjoin(
            WinnerModel, WinnerModel.vk_id == UserModel.vk_id
        ).select().where(WinnerModel.game_id == game_id).gino.load(
            UserModel.distinct(UserModel.id).load(winner=WinnerModel)
        ).first()
        if not user:
            return None
        return User(id=user.id, fio=user.fio, vk_id=user.vk_id, win_count=user.win_count, create_at=user.create_at)
