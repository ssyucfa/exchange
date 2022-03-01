import asyncio
from datetime import datetime
from typing import Union

from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert

from app.base.base_accessor import BaseAccessor
from app.game.models import UserModel, User, GameModel, UsersOfGameModel, BrokerageAccountModel, SecuritiesModel, \
    SecuritiesForGameModel, Securities, VKProfile, Game, BrokerageAccount, SecuritiesForGame
from app.game.schemes import ListUserFinishedRoundSchema
from app.game.text import NO_MONEY, BOUGHT
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
        users_json = ListUserFinishedRoundSchema().dump({'users': users})
        game = await GameModel.create(
            created_at=datetime.now(),
            chat_id=update.object.peer_id,
            round=1,
            users_finished_round=users_json['users'],
            state='GOING'
        )
        _, _, securities = await asyncio.gather(
            self.create_users_of_game(game.id, users),
            self.create_brokerage_accounts_for_users(game.id, users),
            self.create_securities_for_game(game.id)
        )

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
    async def get_going_game(chat_id: int):
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
    async def get_info_about_game(chat_id: int) -> Game:
        res = (await GameModel.outerjoin(
            UsersOfGameModel, GameModel.id == UsersOfGameModel.game_id
        ).outerjoin(
            UserModel, UsersOfGameModel.user_id == UserModel.id
        ).outerjoin(
            SecuritiesForGameModel, GameModel.id == SecuritiesForGameModel.game_id
        ).select().where(
            GameModel.chat_id == chat_id and GameModel.state == 'GOING'
        ).gino.load(
            GameModel.distinct(GameModel.id).load(
                users=UserModel,
                securities=SecuritiesForGameModel
            )
        ).all())[0]

        return Game(
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
                for s in res.securities
            ]
        )

    @staticmethod
    async def is_securities_exist(code: str, chat_id: int) -> Union[SecuritiesForGame, bool]:
        res = (
            await SecuritiesForGameModel.outerjoin(
                GameModel, SecuritiesForGameModel.game_id == GameModel.id
            ).select().where(
                and_(SecuritiesForGameModel.code == code, GameModel.chat_id == chat_id, GameModel.state == 'GOING')
            ).gino.load(
                SecuritiesForGameModel.distinct(SecuritiesForGameModel.id).load(game=GameModel)
            ).all()
        )[0]

        print(res)
        return False if res is None else SecuritiesForGame(**res.to_dict())

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

        cost = securities.cost * int(count)
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
