import typing
from logging import getLogger

from app.game.models import Securities, User, SecuritiesForGame
from app.game.text import *
from app.store.vk_api.dataclasses import Update, Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    @staticmethod
    def get_information_from_securities(securities: typing.Union[list[Securities], list[SecuritiesForGame]]) -> str:
        information = 'Ценные бумаги: '
        for s in securities:
            information += f'{s.description} Code: {s.code} Price for one: {s.cost} '
        return information

    @staticmethod
    def get_information_from_users(users: list[User]) -> str:
        information = 'Участники: '
        for u in users:
            information += f'{u.fio}, '
        return information

    @staticmethod
    def message_buy_is_correct(text: str):
        words = text.split(' ')

        if len(words) == 3 and words[0] == '/buy' and words[2].isdigit():
            return True
        return False

    async def start_game(self, update: Update) -> str:
        if await self.app.store.game.get_going_game(update.object.peer_id):
            return GAME_STARTED

        profiles = await self.app.store.vk_api.get_users(update.object.peer_id)
        if not profiles:
            return WAITING

        securities = await self.app.store.game.prepare_to_start_game(update, profiles)
        return self.get_information_from_securities(securities=securities) + GAME_STARTING

    async def get_info(self, update: Update) -> str:
        if not await self.app.store.game.get_going_game(update.object.peer_id):
            return GAME_NOT_STARTED

        game = await self.app.store.game.get_info_about_game(update.object.peer_id)
        information = self.get_information_from_users(game.users)
        information += self.get_information_from_securities(game.securities)
        information += f'Номер раунда {game.round}'

        return information

    async def buy_securities(self, update: Update) -> str:
        if not self.message_buy_is_correct(update.object.text):
            return WRONG_MESSAGE_FOR_BUY
        if not await self.app.store.game.get_going_game(update.object.peer_id):
            return GAME_NOT_STARTED

        _, code, count = update.object.text.split(' ')

        securities = await self.app.store.game.is_securities_exist(code, update.object.peer_id)
        if not securities:
            return SECURITIES_IS_NOT_EXIST

        vk_id = update.object.user_id
        return await self.app.store.game.buy_securities(vk_id, securities, count)

    async def handle_updates(self, updates: list[Update]):
        if not updates or updates is None:
            return
        for update in updates:
            try:
                information = ''
                if update.object.text == '/start_game':
                    information = await self.start_game(update)
                elif update.object.text == '/info':
                    information = await self.get_info(update)
                elif '/buy' in update.object.text:
                    information = await self.buy_securities(update)
            except Exception as e:
                information = e

            await self.app.store.vk_api.send_message(
                Message(
                    peer_id=update.object.peer_id,
                    text=information
                )
            )

