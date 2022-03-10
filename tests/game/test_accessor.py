from sqlalchemy import and_

from app.game.models import UserModel, GameModel, Game, UsersOfGameModel, BrokerageAccountModel, SecuritiesModel, \
    WinnerModel
from app.game.text import BOUGHT, NO_MONEY, CELLED, DONT_HAVE_SECURITIES, BIG_COUNT, GAME_ENDED, USER_END_ROUND, \
    ALREADY_END_ROUND
from tests.utils import check_empty_table_exists


class TestGameStore:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "game")
        await check_empty_table_exists(cli, "users")
        await check_empty_table_exists(cli, "securities")
        await check_empty_table_exists(cli, "securities_for_game")
        await check_empty_table_exists(cli, "users_of_game")
        await check_empty_table_exists(cli, "brokerage_account")
        await check_empty_table_exists(cli, "event")

    async def test_create_users_or_do_nothing(self, store, profiles):
        users = await store.game.create_users(profiles)
        assert len(users) == 3

        users = await store.game.create_users(profiles)
        assert len(users) == 3

        users = await UserModel.query.gino.all()
        assert len(users) == 3

    async def test_create_game(self, store, users, update_1, securities):
        game_securities = await store.game.create_game(update_1, users)

        assert len(game_securities) == 2
        assert game_securities[0].id == securities[0].id

        game = Game(**(await GameModel.query.gino.first()).to_dict())

        assert game.id == 1
        assert game.chat_id == update_1.object.peer_id
        assert game.state == 'GOING'
        assert game.round == 1
        assert game.users_finished_round.get('1') is False

        users_of_game = await UsersOfGameModel.query.gino.all()

        for user, user_of_game in zip(users, users_of_game):
            assert user_of_game.user_id == user.id
            assert user_of_game.game_id == game.id

        brok_accs = await BrokerageAccountModel.query.gino.all()

        for user, brok_acc in zip(users, brok_accs):
            assert brok_acc.user_id == user.id
            assert brok_acc.game_id == game.id

    async def test_get_going_game(self, store, game_1):
        game = await store.game.get_going_game(game_1.chat_id)

        assert game.id == game_1.id
        assert game.state == game_1.state

    async def test_negative_get_going_game(self, store, game_1):
        await GameModel.update.values({
            'state': 'ENDED'
        }).gino.all()

        game = await store.game.get_going_game(game_1.chat_id)

        assert game is None

    async def test_get_securities(self, store, securities):
        res = await store.game.get_securities()
        assert len(res) == 2
        assert res == securities

        s = await SecuritiesModel.query.where(SecuritiesModel.code == res[0].code).gino.first()
        assert s.id == res[0].id

    async def test_get_game_with_options(self, store, game_1):
        game = await store.game.get_game_with_options(game_1.chat_id)
        assert game.id == game_1.id
        assert len(game.securities) == 2
        assert len(game.users) == 3

    async def test_with_code_get_game_with_options(self, store, game_1):
        game = await store.game.get_game_with_options(game_1.chat_id, game_1.securities[0].code)
        assert game.id == game_1.id
        assert len(game.securities) == 1
        assert len(game.users) == 3

    async def test_negative_with_code_get_game_with_options(self, store, game_1):
        game = await store.game.get_game_with_options(game_1.chat_id, 'lala')
        assert game.id == game_1.id
        assert len(game.securities) == 0
        assert len(game.users) == 3

    async def test_buy_securities(self, store, game_1, user, security):
        old_brok_acc = (await BrokerageAccountModel.query.where(
            and_(BrokerageAccountModel.user_id == user.id, BrokerageAccountModel.game_id == game_1.id)
        ).gino.first()).as_dc()

        new_money = old_brok_acc.money - security.cost * 2
        information = await store.game.buy_securities(user.vk_id, security, 2)
        assert information == BOUGHT + f'У вас в кошельке осталось {new_money}'

        brok_acc = (await BrokerageAccountModel.query.where(
            and_(BrokerageAccountModel.user_id == user.id, BrokerageAccountModel.game_id == game_1.id)
        ).gino.first()).as_dc()

        assert brok_acc != old_brok_acc
        assert brok_acc.money == new_money
        assert brok_acc.securities['COCA'] == 2

    async def test_negative_buy_securities(self, store, game_1, user, security):
        old_brok_acc = (await BrokerageAccountModel.query.where(
            and_(BrokerageAccountModel.user_id == user.id, BrokerageAccountModel.game_id == game_1.id)
        ).gino.first()).as_dc()

        information = await store.game.buy_securities(user.vk_id, security, 20000)
        assert information == NO_MONEY + f'У вас в кошельке {old_brok_acc.money}'

    async def test_two_times_buying_securities(self, store, game_1, user, buying_securities):
        brok_acc = (await BrokerageAccountModel.query.where(
            and_(BrokerageAccountModel.user_id == user.id, BrokerageAccountModel.game_id == game_1.id)
        ).gino.first()).as_dc()
        assert brok_acc.securities['COCA'] == 4

    async def test_cell_securities(self, store, game_1, user, security, buying_securities):
        information = await store.game.cell_securities(user.vk_id, security, 1)

        brok_acc = (await BrokerageAccountModel.query.where(
            and_(BrokerageAccountModel.user_id == user.id, BrokerageAccountModel.game_id == game_1.id)
        ).gino.first()).as_dc()
        assert information == CELLED + f'У вас в кошельке {brok_acc.money}.' \
                                       f' Осталось {security.code}: {brok_acc.securities[security.code]}'

    async def test_negative_cell_securities_no_security_in_broc_acc(
            self, store, game_1, user, security, buying_securities
    ):
        information = await store.game.cell_securities(user.vk_id, game_1.securities[1], 1)
        assert information == DONT_HAVE_SECURITIES

    async def test_negative_cell_securities_bigger_count_than_in_broc_acc(
            self, store, game_1, user, security, buying_securities
    ):
        information = await store.game.cell_securities(user.vk_id, security, 5)
        brok_acc = (await BrokerageAccountModel.query.where(
            and_(BrokerageAccountModel.user_id == user.id, BrokerageAccountModel.game_id == game_1.id)
        ).gino.first()).as_dc()
        assert information == BIG_COUNT + str(brok_acc.securities[security.code])

    async def test_end_game(self, store, game_model_1, users, round_10, events):
        information_for_first = await store.game.end_round(str(users[0].vk_id), game_model_1)
        assert information_for_first == USER_END_ROUND

        information_for_second = await store.game.end_round(str(users[1].vk_id), game_model_1)
        assert information_for_second == USER_END_ROUND

        await store.game.end_round(str(users[2].vk_id), game_model_1)
        assert game_model_1.state == 'ENDED'

        winner = await WinnerModel.query.where(WinnerModel.game_id == game_model_1.id).gino.first()
        assert winner is not None

        user = await UserModel.query.where(UserModel.vk_id == winner.vk_id).gino.first()
        assert user.win_count == 1

    async def test_end_round(self, store, game_model_1, users, events):
        information_for_first = await store.game.end_round(str(users[0].vk_id), game_model_1)
        assert information_for_first == USER_END_ROUND

        information_for_second = await store.game.end_round(str(users[1].vk_id), game_model_1)
        assert information_for_second == USER_END_ROUND

        information_for_end_round = await store.game.end_round(str(users[2].vk_id), game_model_1)
        assert 'Начинается новый раунд.' in information_for_end_round

    async def test_end_round_one_user_2_times_end_round(self, store, game_model_1, user):
        information = await store.game.end_round(str(user.vk_id), game_model_1)
        assert information == USER_END_ROUND

        information = await store.game.end_round(str(user.vk_id), game_model_1)
        assert information == ALREADY_END_ROUND
