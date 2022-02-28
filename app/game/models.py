from dataclasses import dataclass
from datetime import datetime

from app.store.database.gino import db


@dataclass
class User:
    id: int
    vk_id: int
    fio: int
    create_at: datetime


@dataclass
class Profile:
    id: int
    first_name: str
    last_name: str


@dataclass
class Securities:
    id: int
    description: str
    cost: float
    code: str


class UserModel(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer(), primary_key=True)
    vk_id = db.Column(db.Integer(), nullable=False, unique=True)
    fio = db.Column(db.String(), nullable=False)
    create_at = db.Column(db.DateTime(), nullable=False)


class SecuritiesModel(db.Model):
    __tablename__ = 'securities'

    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(), nullable=False)
    cost = db.Column(db.Float(), nullable=False)
    code = db.Column(db.String(), nullable=False)


class SecuritiesForGameModel(db.Model):
    __tablename__ = 'securities_for_game'

    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(), nullable=False)
    cost = db.Column(db.Float(), nullable=False)
    code = db.Column(db.String(), nullable=False)
    game_id = db.Column(db.Integer(), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)


class GameModel(db.Model):
    __tablename__ = 'game'

    id = db.Column(db.Integer(), primary_key=True)
    created_at = db.Column(db.Date(), nullable=False)
    chat_id = db.Column(db.Integer(), nullable=False)
    round = db.Column(db.Integer(), nullable=False)
    users_finished_round = db.Column(db.JSON(), nullable=False)
    state = db.Column(db.String(), nullable=False)


class UsersOfGameModel(db.Model):
    __tablename__ = 'users_of_game'

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)


class BrokerageAccountModel(db.Model):
    __tablename__ = 'brokerage_account'

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.Integer(), db.ForeignKey('game.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    money = db.Column(db.Integer(), nullable=False)
    securities = db.Column(db.JSON())


class EventModel(db.Model):
    __tablename__ = 'event'

    id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.String(), nullable=False)
    diff = db.Column(db.Float(), nullable=False)
