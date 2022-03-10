import pytest

from app.game.models import VKProfile, User, Securities, SecuritiesModel, GameWithOptions, \
    GameModel, EventModel
from app.store.vk_api.dataclasses import Update, UpdateObject


@pytest.fixture
def profiles(store) -> list[VKProfile]:
    return [
        VKProfile(id=1, first_name='Vanya', last_name='Patin'),
        VKProfile(id=2, first_name='Vova', last_name='Putin'),
        VKProfile(id=3, first_name='Aleksei', last_name='Zayac'),
    ]


@pytest.fixture
async def users(store, profiles) -> list[User]:
    yield await store.game.create_users(profiles)


@pytest.fixture
def chat_id_1(store) -> int:
    return 45


@pytest.fixture
def chat_id_2(store) -> int:
    return 34


@pytest.fixture
def update_1(store, chat_id_1) -> Update:
    return Update('action', UpdateObject(1, 1, '', chat_id_1))


@pytest.fixture
def update_2(store, chat_id_2) -> Update:
    return Update('action', UpdateObject(1, 1, '', chat_id_2))


@pytest.fixture
def buy_updates(store, chat_id_1, profiles):
    return [
        Update('action', UpdateObject(1, profiles[0].id, '/buy APPLE 10', chat_id_1)),
        Update('action', UpdateObject(1, profiles[0].id, '/buy APPLE', chat_id_1)),
        Update('action', UpdateObject(1, profiles[0].id, '/buy APPL 10', chat_id_1))
    ]


@pytest.fixture
def cell_updates(store, chat_id_1, profiles):
    return [
        Update('action', UpdateObject(1, profiles[0].id, '/cell APPLE 10', chat_id_1)),
        Update('action', UpdateObject(1, profiles[0].id, '/cell APPLE', chat_id_1)),
        Update('action', UpdateObject(1, profiles[0].id, '/cell APPL 10', chat_id_1))
    ]


@pytest.fixture
async def game_1(store, users, update_1, securities) -> GameWithOptions:
    await store.game.create_game(update_1, users)
    yield await store.game.get_game_with_options(update_1.object.peer_id)


@pytest.fixture
async def game_2(store, users, update_2, securities) -> GameWithOptions:
    await store.game.create_game(update_2, users)
    return await store.game.get_game_with_options(update_2.object.peer_id)


@pytest.fixture
def security(store, game_1):
    return game_1.securities[0]


@pytest.fixture
def user(users):
    return users[0]


@pytest.fixture
async def securities(store) -> list[Securities]:
    yield [
        Securities(**(await SecuritiesModel.create(description='apple corporation', cost=10, code='APPLE')).to_dict()),
        Securities(**(await SecuritiesModel.create(description='coca-cola corp', cost=10, code='COCA')).to_dict())
    ]


@pytest.fixture
async def buying_securities(store, game_1, user, security):
    await store.game.buy_securities(user.vk_id, security, 2)
    await store.game.buy_securities(user.vk_id, security, 2)


@pytest.fixture
async def round_10(store, game_1, game_model_1, users):
    await store.game.buy_securities(users[0].vk_id, game_1.securities[0], 2)
    await store.game.buy_securities(users[1].vk_id, game_1.securities[1], 2)
    await game_model_1.update(round=10).apply()


@pytest.fixture
async def game_model_1(store, game_1):
    yield await GameModel.query.where(GameModel.id == game_1.id).gino.first()


@pytest.fixture
async def events(store):
    yield await EventModel.insert().gino.all([
            {'text': 'some case 1', 'diff': 1.1},
            {'text': 'some case 2', 'diff': 0.9},
            {'text': 'some case 3', 'diff': 1.4},
            {'text': 'some case 4', 'diff': 0.7},
        ])


