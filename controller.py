import enum
import time

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from email_validator import validate_email, EmailNotValidError

from fastapi import status, HTTPException

import models

engine = create_async_engine("sqlite+aiosqlite:///./app.db", connect_args={"check_same_thread": False})
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def on_start():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


async def on_stop():
    await engine.dispose()


async def add_row(model: models.Base) -> models.Base:
    async with async_session() as session:
        session.add(model)
        await session.commit()
        return model


@enum.unique
class IsNameOrEmailResult(enum.IntEnum):
    NOTHING_EXIST = 0
    NAME_EXIST = 1
    EMAIL_EXIST = 2
    BOTH_EMAIL_AND_NAME_EXIST = 3


async def is_name_or_email_exist(name: str, email: str) -> IsNameOrEmailResult:
    async with async_session() as session:
        async def check_name_exist() -> bool:
            if await session.scalar(select(models.User).where(models.User.name == name)) is not None:
                return True
            return False

        async def check_email_exist() -> bool:
            if await session.scalar(select(models.User).where(models.User.email == email)) is not None:
                return True
            return False

        name_exist = await check_name_exist()
        email_exist = await check_email_exist()
        match name_exist, email_exist:
            case False, False:
                return IsNameOrEmailResult.NOTHING_EXIST
            case True, False:
                return IsNameOrEmailResult.NAME_EXIST
            case False, True:
                return IsNameOrEmailResult.EMAIL_EXIST
            case True, True:
                return IsNameOrEmailResult.BOTH_EMAIL_AND_NAME_EXIST


async def is_name_exist(name: str) -> bool:
    async with async_session() as session:
        result = await session.scalar(select(models.User).where(models.User.name == name))
        if result is not None:
            return True
        return False


async def is_email_exist(email: str):
    async with async_session() as session:
        result = await session.scalar(select(models.User).where(models.User.email == email))
        if result is not None:
            return True
        return False


async def get_user(name_or_email: str) -> models.User | None:
    async with async_session() as session:
        try:
            validate_email(name_or_email)
            result = await session.scalar(select(models.User).where(models.User.email == name_or_email))
            if result is None:
                raise EmailNotValidError
            else:
                return result
        except EmailNotValidError:
            return await session.scalar(select(models.User).where(models.User.name == name_or_email))


async def get_user_by_id(user_id: int) -> models.User | None:
    async with async_session() as session:
        return await session.scalar(select(models.User).where(models.User.id == user_id))


async def update_active_time(session_uuid: str, user_id: int):
    async with async_session() as session:
        session_object = await session.scalar(select(models.Session).where(models.Session.uuid == session_uuid))
        user = await session.scalar(select(models.User).where(models.User.id == user_id))
        try:
            session_object.last_active = user.last_active = time.time()
        except AttributeError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        await session.commit()


async def is_session_exist(session_uuid: str, user_id: int) -> bool:
    async with (async_session() as session):
        if await session.scalar(
                select(models.Session)
                .where(models.Session.uuid == session_uuid)
                .where(models.Session.user_id == user_id)
        ) is not None:
            return True
        else:
            return False
