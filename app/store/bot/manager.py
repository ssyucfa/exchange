import typing
from logging import getLogger

from app.game.models import Securities
from app.store.vk_api.dataclasses import Update, Message

if typing.TYPE_CHECKING:
    from app.web.app import Application

TEXT = {
    'game_started': 'Игра уже идет! Следите за игрой!',
    'game_starting': 'Игра началась! Для покупки акций пишите "/buy <code> <count>"'
}


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    @staticmethod
    async def get_information_from_securities(securities: list[Securities]) -> str:
        information = ''''''
        for s in securities:
            information += f'{s.description} Code: {s.code} Price for one: {s.cost} '
        return information

    async def start_game(self, update: Update):
        if await self.app.store.game.get_going_game(update.object.peer_id):
            information = TEXT['game_started']
        else:
            profiles = await self.app.store.vk_api.get_users(update.object.peer_id)
            if not profiles:
                information = 'Подождите немного, вк не отвечает'
            else:
                await self.app.store.game.prepare_to_start_game(update, profiles)

                securities = await self.app.store.game.get_securities()
                information = (await self.get_information_from_securities(securities=securities)
                               + TEXT['game_starting']
                               )

        return information

    async def handle_updates(self, updates: list[Update]):
        if not updates or updates is None:
            return
        for update in updates:
            if update.object.text == '/start_game':
                try:
                    information = await self.start_game(update)
                except Exception as e:
                    information = e

                await self.app.store.vk_api.send_message(
                    Message(
                        peer_id=update.object.peer_id,
                        text=information
                    )
                )