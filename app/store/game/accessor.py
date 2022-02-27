from datetime import datetime

from app.base.base_accessor import BaseAccessor
from app.game.models import UserModel, User, GameModel, UsersOfGameModel, BrokerageAccountModel, SecuritiesModel, \
    SecuritiesForGameModel
from app.game.schemes import ListUserFinishedRoundSchema
from app.store.vk_api.dataclasses import Update
from app.web.app import Application


class GameAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        await app.database.connect()

    async def prepare_to_start_game(self, update: Update, profiles: dict):
        users = await self.create_users(profiles)
        await self.create_game(update, users)

    async def create_users(self, profiles: dict) -> list[User]:
        users = []
        for profile in profiles:
            try:
                user = await UserModel.create(
                    vk_id=profile['id'],
                    fio=f'{profile["first_name"]} {profile["last_name"]}',
                    create_at=datetime.now()
                )
                users.append(user)
            except Exception as e:
                self.logger.error(e)

                user = await UserModel.query.where(UserModel.vk_id == profile['id']).gino.first()
                users.append(user)
        return users

    async def create_game(self, update: Update, users: list[User]):
        try:

            users = ListUserFinishedRoundSchema().dump({'users': users})
            game = await GameModel.create(
                created_at=datetime.now(),
                chat_id=update.object.peer_id,
                round=1,
                users_finished_round=users['users'],
                state='GOING'
            )

            await self.create_users_of_game(game.id, users['users'])
            await self.create_brokerage_accounts_for_users(game.id, users['users'])
            await self.create_securities_for_game(game.id)
        except Exception as e:
            self.logger.error(e)

    @staticmethod
    async def create_users_of_game(game_id: int, users: list[dict]):
        await UsersOfGameModel.insert().gino.all(
            [
                {
                    'game_id': game_id,
                    'user_id': user['id']
                }
                for user in users
            ]
        )

    @staticmethod
    async def create_brokerage_accounts_for_users(game_id: int, users: list[dict]):
        await BrokerageAccountModel.insert().gino.all(
            [
                {
                    'game_id': game_id,
                    'user_id': user['id'],
                    'money': 1000,
                    'securities': {}
                }
                for user in users
            ]
        )

    @staticmethod
    async def create_securities_for_game(game_id: int):
        securities = await SecuritiesModel.query.gino.all()

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
    async def get_going_game_by_chat_id(chat_id: int):
        game = await GameModel.query.where(
            GameModel.chat_id == chat_id and GameModel.state == 'GOING'
        ).gino.first()

        return game

    @staticmethod
    async def get_securities():
        return await SecuritiesModel.query.gino.all()
