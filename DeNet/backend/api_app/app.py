from contextlib import asynccontextmanager
from typing import Annotated
import uuid

from fastapi import FastAPI, File, Path, Request, UploadFile, status, Header, Body
from . import schemas


from ..db import database, models, db_utils
from ..db.models import Storage
from ..settings import DEBUG
from .app_depends import Session, Media_path, User, MEDIA_PATH
from ..services.file_service import write_to_disk


@asynccontextmanager
async def database_init(app: FastAPI):
    engine = database.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    debug=DEBUG, lifespan=database_init
)


"""
1. Серверная часть:
- Реализовать API для следующих действий:
- POST /upload: загрузка файла на сервер
- GET /download: скачивание файла с сервера
"""

@app.get('/hello',
         )
async def hello() -> schemas.Hello:

    answer = schemas.Hello(name="Hello world!")
    return answer


@app.get('/storage',
         response_model=schemas.StorageList,
         tags=["STORAGE"],
         status_code=status.HTTP_200_OK,
         )
async def get_storage_list(user: User,
                       orm_session: Session,
                       ) -> schemas.StorageList:
    storage_list = await db_utils.get_user_storage(user, orm_session)

    answer_schema = [
        schemas.StorageBaseOut.model_validate(storage) for storage in storage_list.unique()
    ]
    return schemas.StorageList(storage_list = answer_schema)


@app.get('/download',
         response_model=schemas.StorageOut,
         tags=["STORAGE"],
         status_code=status.HTTP_200_OK,
         )
async def get_storage(user: User,
                      orm_session: Session,
                      storage: schemas.StorageBase
                       ) -> schemas.StorageOut:

    storage = await db_utils.get_by_id(Storage, storage.id, orm_session)
    if storage.user_id != user.id:
        raise Exception("Forbiden")
    cells = [
        schemas.CellBase.model_validate(cell) for cell in storage.cells
    ]
    answer = schemas.StorageOut.model_validate(storage)
    return answer


@app.post(
    "/upload_init",
    response_model=schemas.Upload_init_out,
    tags=["UPLOAD"],
    status_code=status.HTTP_201_CREATED,
    # responses=schemas.error_responses,
)
async def post_init_upload(
    request: Request,
    storage: schemas.Upload_init_in,
    orm_session: Session,
    user: User,
    static_path: Media_path,
) -> schemas.Upload_init_out:
    """Endpoint for create an storage"""
    # path = await write_to_disk(user, file, static_path)
    new_storage = models.Storage(user=user, name=storage.name, size=storage.size)
    pk = await db_utils.save(new_storage, orm_session)
    uuid_session = uuid.uuid4()
    new_session = models.UploadSession(storage_id=pk, session=uuid_session)
    orm_session.add(new_session)
    # await session.flush((new_session, ))
    # session_id = new_session.session
    await orm_session.commit()
    return schemas.Upload_init_out(pk=pk, session=str(uuid_session))



@app.post(
    "/upload",
    response_model=schemas.Upload_out,
    tags=["UPLOAD"],
    status_code=status.HTTP_201_CREATED,
    # responses=schemas.error_responses,
)
async def upload(
    request: Request,
    orm_session: Session,
    session: Annotated[str, Header(..., )],
    number: Annotated[int, Body(..., )],
    user: User,
    static_path: Media_path,
    file: Annotated[
        UploadFile, File(..., description="image file", title="FILE")
    ],
) -> schemas.Upload_out:
    """Endpoint for upload file"""
    upload_session = await db_utils.get_one(models.UploadSession, orm_session, session=session)
    storage: Storage = upload_session.storage
    cells = storage.cells
    addresses = [cell.address for cell in cells]
    if number not in addresses:
    # cell = await db_utils.get_one(models.Cell, orm_session, address=number, storage_id=storage.id)
        path = await write_to_disk(user, file, media_path=static_path, storage=storage, address=number)
        memory_cell = models.Cell(path=path, address=number, storage=storage)
        await db_utils.save(memory_cell, orm_session)
    else:
        raise Exception("this address is already exists")
    return schemas.Upload_out(result=True)