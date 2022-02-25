import typing
from hashlib import sha256
from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.admin.models import AdminModel

if typing.TYPE_CHECKING:
    from app.web.app import Application


class AdminAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        await super().connect(app)
        await app.database.connect()
        await self.create_admin(
            email=app.config.admin.email, password=app.config.admin.password
        )

    async def get_by_email(self, email: str) -> Optional[AdminModel]:
        admin = await AdminModel.query.where(AdminModel.email == email).limit(1).gino.first()
        return admin

    async def create_admin(self, email: str, password: str) -> AdminModel:
        admin = await AdminModel.create(email=email, password=sha256(password.encode()).hexdigest())
        return admin
