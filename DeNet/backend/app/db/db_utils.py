from typing import Union, Type

from sqlalchemy import select, ScalarResult
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession

from . import models

Model = Union[
    models.User,
    models.Storage,
    models.UploadSession,
    models.Cell
]
ModelType = Type[Model]


class CRUDException(Exception): ...  # noqa E701


class InstanceNotExists(CRUDException): ...  # noqa E701


async def save(new_instance: Model, session: AsyncSession) -> int:
    """Сохраняет объекта в БД, возвращает id"""
    session.add(new_instance)
    await session.flush((new_instance,))
    id = new_instance.id
    await session.commit()
    return id


async def delete(instance: Model, session: AsyncSession) -> None:
    """Удаляет объект из БД"""
    await session.delete(instance)


async def get_by_id(
    model: ModelType, instance_id: int, session: AsyncSession, **kwargs
) -> Model:
    """Получает объект из БД по его id, если объект не найден
    вызывает исключение"""
    instance: Model | None = await session.get(model, instance_id, **kwargs)
    if not instance:
        raise InstanceNotExists(f"{model.__name__} does not exists")
    return instance


async def get_one(model: ModelType, session_orm: AsyncSession, **kwargs) -> Model:
    """Получает объект из БД по его уникальному набору полей,
    если объект не найдет или подходящих объектов больше вызывает ошибку"""
    fields = {c.name: c for c in model.__table__.columns}
    search_kwargs = {}
    for k, v in kwargs.items():
        if k in fields:
            search_kwargs[fields[k]] = v
        else:
            raise CRUDException(f"{model.__name__} has not column {k}")
    instance = await session_orm.scalars(
        select(model).where(*(k == v for k, v in search_kwargs.items()))
    )
    try:
        one_instance: Model = instance.unique().one_or_none()
    except MultipleResultsFound:
        raise CRUDException(
            f"{model.__name__} with "
            f"{tuple(f'{k.name} = {v}' for k, v in search_kwargs.items())} "
            f"is not unique"
        )
    if not one_instance:
        raise InstanceNotExists(
            f"{model.__name__} does not exists with "
            f"{tuple(f'{k.name} = {v}' for k, v in search_kwargs.items())}"
        )
    return one_instance


async def get_user_storage(
    user: models.User, session: AsyncSession
) -> ScalarResult[models.Storage]:
    """Получает список хранилища пользователя"""
    stmt = select(models.Storage).filter(models.Storage.user_id == user.id).order_by(models.Storage.id.desc())
    return await session.scalars(stmt)
