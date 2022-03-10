from marshmallow import Schema, fields


class WinnerSchema(Schema):
    vk_id = fields.Integer()


class GameSchema(Schema):
    id = fields.Integer()
    created_at = fields.DateTime()
    chat_id = fields.Integer()
    round = fields.Integer()
    state = fields.String()
    winner = fields.Nested(WinnerSchema)


class ListGameSchema(Schema):
    games = fields.Nested(GameSchema, many=True)
    limit = fields.Integer()
    page = fields.Integer()


class PaginationSchema(Schema):
    limit = fields.Integer()
    page = fields.Integer()


class GetGameSchema(Schema):
    game_id = fields.Integer(required=True)


class UserSchema(Schema):
    vk_id = fields.Integer()
    win_count = fields.Integer()
    fio = fields.String()
