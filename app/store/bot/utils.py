from app.game.text import GAME_NOT_STARTED
from app.store.vk_api.dataclasses import Update


def only_for_going_game(func):
    async def wrapper(self, update: Update):
        if not await self.app.store.game.get_going_game(update.object.peer_id):
            return GAME_NOT_STARTED
        return await func(self, update)
    return wrapper
