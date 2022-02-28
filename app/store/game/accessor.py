from datetime import datetime

from sqlalchemy.dialects.postgresql import insert

from app.base.base_accessor import BaseAccessor
from app.game.models import UserModel, User, GameModel, UsersOfGameModel, BrokerageAccountModel, SecuritiesModel, \
    SecuritiesForGameModel, Securities
from app.game.schemes import ListUserFinishedRoundSchema
from app.store.vk_api.dataclasses import Update
from app.web.app import Application


class GameAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        await app.database.connect()

    async def prepare_to_start_game(self, update: Update, profiles: dict):
        users = await self.create_users(profiles)
        await self.create_game(update, users)

    @staticmethod
    async def create_users(profiles: dict) -> list[User]:
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

    async def create_game(self, update: Update, users: list[User]):
        users_json = ListUserFinishedRoundSchema().dump({'users': users})
        game = await GameModel.create(
            created_at=datetime.now(),
            chat_id=update.object.peer_id,
            round=1,
            users_finished_round=users_json['users'],
            state='GOING'
        )
        print(users)
        await self.create_users_of_game(game.id, users)
        await self.create_brokerage_accounts_for_users(game.id, users)
        await self.create_securities_for_game(game.id)

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

    async def create_securities_for_game(self, game_id: int):
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

    @staticmethod
    async def get_going_game(chat_id: int):
        game = await GameModel.query.where(
            GameModel.chat_id == chat_id and GameModel.state == 'GOING'
        ).gino.first()

        return game

    @staticmethod
    async def get_securities() -> list[Securities]:
        res = await SecuritiesModel.query.gino.all()

        return [
            Securities(**s.to_dict())
            for s in res
        ]
