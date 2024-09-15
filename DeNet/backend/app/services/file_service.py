from pathlib import Path

import aiofiles
from fastapi import UploadFile

from ..db.models import User, Storage


async def write_to_storage(user: User, file: UploadFile, storage_path:str, storage: Storage, address: int) -> str:
    # with open(f'{MEDIA_PATH}/user_{user.id}/storage_{storage.id}', "rb") as file:
    #     file.write(data)
    path = Path(f"user_{user.id}/storage_{storage.id}")
    absolute_path = Path(storage_path).absolute() / path
    absolute_path.mkdir(exist_ok=True, parents=True)
    if file.filename:
        file_path = path / f'{address}_{file.filename}'
    else:
        file_path = path / f'{address}_UPLOAD'
    content = await file.read()
    async with aiofiles.open(storage_path / file_path, mode="wb") as f:
        await f.write(content)
    return str(file_path)
