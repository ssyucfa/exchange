class TestGameViews:
    async def test_get_games(self, game_1, game_2, authed_cli):
        resp = await authed_cli.get(
            '/admin.fetch_games?limit=1&page=2',
        )

        assert resp.status == 200
        assert (await resp.json())['data'] == {
            "limit": 1,
            "games": [
                {
                    "state": "GOING",
                    "created_at": game_2.created_at.isoformat(),
                    "winner": None,
                    "round": game_2.round,
                    "id": game_2.id,
                    "chat_id": game_2.chat_id
                }
            ],
            "page": 2
        }

    async def test_negative_get_games_no_authorized(self, cli):
        resp = await cli.get(
            '/admin.fetch_games?limit=1&page=2',
        )

        assert resp.status == 401

    async def test_get_game_stats(self, store, authed_cli, game_1, round_10, users, game_model_1):
        await store.game.end_round(str(users[0].vk_id), game_model_1)
        await store.game.end_round(str(users[1].vk_id), game_model_1)
        await store.game.end_round(str(users[2].vk_id), game_model_1)

        resp = await authed_cli.get(
            f'/admin.fetch_game_stats?game_id={game_1.id}',
        )

        assert resp.status == 200

    async def test_negative_get_game_stats_unknown_game_id(self, authed_cli):
        resp = await authed_cli.get(
            '/admin.fetch_game_stats?game_id=432423',
        )

        assert resp.status == 400

    async def test_negative_get_game_no_authorized(self, cli):
        resp = await cli.get(
            '/admin.fetch_game_stats?game_id=432423',
        )

        assert resp.status == 401