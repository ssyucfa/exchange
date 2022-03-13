from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from app.store.database.gino import db


@dataclass
class BrokerageAccount:
    id: int
    game_id: int
    user_id: int
    money: float
    securities: dict[str, int]


@dataclass
class User:
    id: int
    vk_id: int
    fio: str
    create_at: datetime
    win_count: int


@dataclass
class Event:
    id: int
    text: str
    diff: float


@dataclass
class VKProfile:
    id: int
    first_name: str
    last_name: str


@dataclass
class Securities:
    id: int
    description: str
    cost: float
    code: str


@dataclass
class SecuritiesForGame:
    id: int
    description: str
    cost: float
    code: str
    game_id: int


@dataclass
class Game:
    id: int
    created_at: datetime
    chat_id: int
    round: int
    users_finished_round: dict
    state: str


@dataclass
class GameWithOptions(Game):
    users: list[User]
    securities: list[SecuritiesForGame]


@dataclass
class Winner:
    vk_id: int


@dataclass
class GameWithWinner(Game):
    winner: Optional[dict[Winner]] = None


class WinnerModel(db.Model):
    __tablename__ = 'winners'

    id = db.Column(db.Integer(), primary_key=True)
    vk_id = db.Column(db.Integer(), db.ForeignKey('users.vk_id'), nullable=False)
    game_id = db.Column(db.Integer(), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    vk_id = db.Column(db.Integer(), nullable=False, unique=True)
    fio = db.Column(db.String(), nullable=False)
    create_at = db.Column(db.DateTime(), nullable=False)
    win_count = db.Column(db.Integer(), default=0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._winner: Optional[WinnerModel] = None

    @property
    def winner(self) -> Optional[WinnerModel]:
        return self._winner

    @winner.setter
    def winner(self, val: Optional[WinnerModel]):
        if val is not None:
            self._winner = val


class SecuritiesModel(db.Model):
    __tablename__ = 'securities'

    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(), nullable=False)
    cost = db.Column(db.Float(), nullable=False)
    code = db.Column(db.String(), nullable=False, unique=True)

    def as_dc(self):
        return Securities(**self.to_dict())


class SecuritiesForGameModel(db.Model):
    __tablename__ = 'securities_for_game'

    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(), nullable=False)
    cost = db.Column(db.Float(), nullable=False)
    code = db.Column(db.String(), nullable=False)
    game_id = db.Column(db.Integer(), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._game: Optional['GameModel'] = None

    @property
    def game(self) -> 'GameModel':
        return self._game

    @game.setter
    def game(self, val: Optional['GameModel']):
        if val is not None:
            self._game = val


class GameModel(db.Model):
    __tablename__ = 'game'

    id = db.Column(db.Integer(), primary_key=True)
    created_at = db.Column(db.Date(), nullable=False)
    chat_id = db.Column(db.Integer(), nullable=False)
    round = db.Column(db.Integer(), nullable=False)
    users_finished_round = db.Column(db.JSON(), nullable=False)
    state = db.Column(db.String(), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._users: list['UserModel'] = []
        self._winner: Optional[WinnerModel] = None
        self._users_id: list[int] = []
        self._securities_id: list[int] = []
        self._securities: list['SecuritiesForGame'] = []

    @property
    def users(self) -> list[UserModel]:
        return self._users

    @property
    def winner(self) -> Optional[WinnerModel]:
        return self._winner

    @property
    def securities(self) -> list['SecuritiesForGame']:
        return self._securities

    @securities.setter
    def securities(self, val: Optional['SecuritiesForGame']):
        if val is not None and val.id not in self._securities_id:
            self._securities_id.append(val.id)
            self._securities.append(val)

    @users.setter
    def users(self, val: Optional['UserModel']):
        if val is not None and val.id not in self._users_id:
            self._users_id.append(val.id)
            self._users.append(val)

    @winner.setter
    def winner(self, val: Optional[WinnerModel]):
        if val is not None:
            self._winner = val


class UsersOfGameModel(db.Model):
    __tablename__ = 'users_of_game'

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)


class BrokerageAccountModel(db.Model):
    __tablename__ = 'brokerage_account'

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    money = db.Column(db.Float(), nullable=False)
    securities = db.Column(db.JSON())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._user: Optional['UserModel'] = None

    @property
    def user(self) -> 'UserModel':
        return self._user

    @user.setter
    def user(self, val: Optional['UserModel']):
        if val is not None:
            self._user = val

    def as_dc(self) -> BrokerageAccount:
        return BrokerageAccount(**self.to_dict())


class EventModel(db.Model):
    __tablename__ = 'event'

    id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.String(), nullable=False)
    diff = db.Column(db.Float(), nullable=False)