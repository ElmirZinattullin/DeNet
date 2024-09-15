from typing import Annotated

from fastapi import Depends, Header, HTTPException

from ..db import models, db_utils
from ..db.database import AsyncSession, get_db_session

MEDIA_PATH = "storage"


async def get_session():
    # print("session start")
    session = get_db_session()()
    try:

        # with session.begin():
        yield session
    # print("close_session")
    finally:
        await session.close()


async def get_user(
    api_key: Annotated[
        str, Header(..., description="api-key for user authentication")
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
):

    try:
        user = await db_utils.get_one(models.User, session, api_key=api_key)
    except db_utils.CRUDException:
        raise HTTPException(status_code=401, detail="Wrong api-key")
    return user


async def get_media_path():
    path = MEDIA_PATH
    # path = f'{path}'
    return path


Session = Annotated[AsyncSession, Depends(get_session)]
User = Annotated[models.User, Depends(get_user)]
Media_path = Annotated[str, Depends(get_media_path)]
