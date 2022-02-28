from marshmallow import Schema, fields


class UserFinishedRoundSchema(Schema):
    id = fields.Integer()
    vk_id = fields.Integer()
    is_finished = fields.Bool(default=False)


class ListUserFinishedRoundSchema(Schema):
    users = fields.Nested(UserFinishedRoundSchema, many=True)
