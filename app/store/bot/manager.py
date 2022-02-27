import typing
from logging import getLogger

from app.store.vk_api.dataclasses import Update, Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    @staticmethod
    async def get_information_for_players_from_securities(securities) -> str:
        information = ''''''
        for s in securities:
            information += f'{s.description} Code: {s.code} Price for one: {s.cost} '
        return information

    async def handle_updates(self, updates: list[Update]):
        if not updates or updates is None:
            return
        for update in updates:
            if update.object.text == '/start_game':
                if await self.app.store.game.get_going_game_by_chat_id(update.object.peer_id):
                    await self.app.store.vk_api.send_message(
                        Message(
                            peer_id=update.object.peer_id,
                            text='Игра уже идет! Следите за игрой!'
                        )
                    )
                    break
                profiles = await self.app.store.vk_api.get_users(update.object.peer_id)
                await self.app.store.game.prepare_to_start_game(update, profiles)

                securities = await self.app.store.game.get_securities()
                information = await self.get_information_for_players_from_securities(securities=securities)

                await self.app.store.vk_api.send_message(
                    Message(
                        peer_id=update.object.peer_id,
                        text=information + 'Игра началась! Для покупки акций пишите "/buy <code> <count>"'
                    )
                )
