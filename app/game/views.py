from aiohttp_apispec import querystring_schema, request_schema
from aiohttp.web_exceptions import HTTPBadRequest

from app.game.schemes import ListGameSchema, PaginationSchema, GetGameSchema, UserSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ListGameView(AuthRequiredMixin, View):
    @querystring_schema(PaginationSchema)
    async def get(self):
        limit = self.request['querystring'].get('limit', 10)
        page = self.request['querystring'].get('page', 1)

        games = await self.store.game.get_games_with_winners(
            limit,
            page
        )

        return json_response(data=ListGameSchema().dump({
            'games': games,
            'limit': limit,
            'page': page
        }))


class GameWinnerView(AuthRequiredMixin, View):
    @querystring_schema(GetGameSchema)
    async def get(self):
        game_id = self.request['querystring'].get('game_id')
        user = await self.store.game.get_winner_by_game_id(game_id)
        if not user:
            raise HTTPBadRequest

        return json_response(data=UserSchema().dump(user))
