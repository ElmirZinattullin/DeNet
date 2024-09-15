from contextlib import asynccontextmanager

from typing import Annotated
import uuid

from fastapi import FastAPI, File, Request, UploadFile, status, Header, Body
from fastapi.responses import RedirectResponse, JSONResponse
from . import schemas


from ..db import database, models, db_utils
from ..db.models import Storage, Cell
from ..settings import DEBUG
from .app_depends import Session, Media_path, User
from ..services.file_service import write_to_storage


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
@app.exception_handler(db_utils.InstanceNotExists)
async def http_instance_not_exist_exception_handler(request, exc):
    answer = schemas.Error(
        result=False, error_type=exc.__class__.__name__, error_message=str(exc)
    )
    return JSONResponse(answer.model_dump(), status.HTTP_404_NOT_FOUND)


@app.exception_handler(db_utils.CRUDException)
async def http_crud_exception_handler(request, exc):
    answer = schemas.Error(
        result=False, error_type=exc.__class__.__name__, error_message=str(exc)
    )
    return JSONResponse(answer.model_dump(), status.HTTP_403_FORBIDDEN)



# if DEBUG:
#     @app.get('/api/hello',
#              )
#     async def hello() -> schemas.Hello:
#
#         answer = schemas.Hello(name="Hello world!")
#         return answer


@app.get('/download/{file_path:path}',
         tags=["DOWNLOAD"],
         )
async def redirect_file(request: Request, file_path:str, user: User, session_orm: Session) :
    host = request.client.host
    cell = await db_utils.get_one(Cell, session_orm, path=file_path)
    if cell.storage.user_id == user.id:
        return RedirectResponse(
            url=f"http://{host}/storage/{file_path}", status_code=status.HTTP_302_FOUND,
            headers={"X-Accel-Redirect": f"/storage/{file_path}"}
        )
    else:
        raise db_utils.CRUDException("You don't have access")


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


@app.get('/download_init',
         response_model=schemas.StorageOut,
         tags=["DOWNLOAD"],
         status_code=status.HTTP_200_OK,
         )
async def get_storage(user: User,
                      orm_session: Session,
                      storage: schemas.StorageBase
                       ) -> schemas.StorageOut:

    storage = await db_utils.get_by_id(Storage, storage.id, orm_session)
    if storage.user_id != user.id:
        raise db_utils.CRUDException("You don't have access")
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
    return schemas.Upload_init_out(result=True, pk=pk, session=str(uuid_session))


@app.post(
    "/register",
    response_model=schemas.RegisterOut,
    tags=["USER"],
    status_code=status.HTTP_201_CREATED,
    # responses=schemas.error_responses,
)
async def post_register(
    request: Request,
    register: schemas.Register,
    orm_session: Session,
) -> schemas.RegisterOut:
    """Endpoint for create a user"""
    # path = await write_to_disk(user, file, static_path)
    user = await db_utils.get_one(models.User, orm_session, api_key=register.api_key)
    if user:
        raise db_utils.CRUDException("User has already exist")
    new_user = models.User(name=register.name, api_key=register.api_key)
    pk = await db_utils.save(new_user, orm_session)
    return schemas.RegisterOut(result=True)



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
    storage_path: Media_path,
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
        path = await write_to_storage(user, file, storage_path=storage_path, storage=storage, address=number)
        memory_cell = models.Cell(path=path, address=number, storage=storage)
        await db_utils.save(memory_cell, orm_session)
    else:
        raise db_utils.CRUDException("this address is already exists")
    return schemas.Upload_out(result=True)