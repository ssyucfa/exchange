import pytest

from app.game.text import GAME_NOT_STARTED, USER_IS_NOT_PLAYING, WRONG_MESSAGE_FOR_BUY, SECURITIES_IS_NOT_EXIST, \
    WRONG_MESSAGE_FOR_CELL, GAME_STARTING, GAME_STARTED, WAITING
from app.store.vk_api.dataclasses import Update, UpdateObject


class TestBotsManager:
    @pytest.mark.parametrize(
        'text, expected_result', (
                ('/buy a 10', True),
                ('/by a 10', False),
                ('/buy a some', False),
                ('/buy a', False),
        )
    )
    async def test_message_buy_is_correct(self, store, text, expected_result):
        result = store.bots_manager.message_buy_is_correct(text)
        assert result == expected_result

    @pytest.mark.parametrize(
        'text, expected_result', (
                ('/cell a 10', True),
                ('/cl a 10', False),
                ('/cell a some', False),
                ('/cell a', False),
        )
    )
    async def test_message_cell_is_correct(self, store, text, expected_result):
        result = store.bots_manager.message_cell_is_correct(text)
        assert result == expected_result

    async def test_start_game(self, store, update_1, securities, profiles):
        information = await store.bots_manager.start_game(update_1, profiles)
        assert information == store.bots_manager.get_information_from_securities(securities) + GAME_STARTING

    async def test_negative_start_game_game_started(self, store, update_1, game_1, profiles):
        information = await store.bots_manager.start_game(update_1, profiles)
        assert information == GAME_STARTED

    async def test_negative_start_game_no_profiles(self, store, update_1):
        information = await store.bots_manager.start_game(update_1, [])
        assert information == WAITING

    async def test_get_info(self, store, update_1, game_1):
        information = await store.bots_manager.get_info(update_1)
        assert f'Номер раунда {game_1.round}' in information

    async def test_negative_get_info(self, store, update_2, game_1):
        information = await store.bots_manager.get_info(update_2)
        assert information == GAME_NOT_STARTED

    async def test_negative_buy_securities_wrong_message(self, store, game_1, buy_updates):
        information = await store.bots_manager.buy_securities(buy_updates[1])
        assert information == WRONG_MESSAGE_FOR_BUY

    async def test_negative_buy_securities_security_is_not_exist(self, store, game_1, buy_updates):
        information = await store.bots_manager.buy_securities(buy_updates[2])
        assert information == SECURITIES_IS_NOT_EXIST

    async def test_negative_buy_securities_game_not_started(self, store, buy_updates):
        information = await store.bots_manager.buy_securities(buy_updates[0])
        assert information == GAME_NOT_STARTED

    async def test_negative_cell_securities_wrong_message(self, store, game_1, cell_updates):
        information = await store.bots_manager.cell_securities(cell_updates[1])
        assert information == WRONG_MESSAGE_FOR_CELL

    async def test_negative_cell_securities_security_is_not_exist(self, store, game_1, cell_updates):
        information = await store.bots_manager.cell_securities(cell_updates[2])
        assert information == SECURITIES_IS_NOT_EXIST

    async def test_negative_cell_securities_game_not_started(self, store, cell_updates):
        information = await store.bots_manager.cell_securities(cell_updates[0])
        assert information == GAME_NOT_STARTED

    async def test_negative_end_round(self, store, update_1):
        information = await store.bots_manager.end_round(update_1)
        assert information == GAME_NOT_STARTED

    async def test_negative_buy_user_is_not_playing(self, store, game_1, chat_id_1):
        update = Update('action', UpdateObject(1, 5342, '/buy APPLE 10', chat_id_1))
        information = await store.bots_manager.buy_securities(update)
        assert information == USER_IS_NOT_PLAYING

    async def test_negative_cell_user_is_not_playing(self, store, game_1, chat_id_1):
        update = Update('action', UpdateObject(1, 5342, '/cell APPLE 10', chat_id_1))
        information = await store.bots_manager.cell_securities(update)
        assert information == USER_IS_NOT_PLAYING
    
    async def test_negative_end_round_user_is_not_playing(self, store, game_1, chat_id_1):
        update = Update('action', UpdateObject(1, 5342, '/end_round', chat_id_1))
        information = await store.bots_manager.end_round(update)
        assert information == USER_IS_NOT_PLAYING
