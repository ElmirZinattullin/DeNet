from typing import Annotated, List
from fastapi import Body
from pydantic import BaseModel, ConfigDict


class Hello(BaseModel):
    name: str


class Upload_init_in(BaseModel):
    size: int
    name: str
    pass


class Upload_in(BaseModel):
    address: int
    storage_id: str
    pass


class Upload_out(BaseModel):
    result: bool
    pass

class StorageBase(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)

class StorageBaseOut(BaseModel):
    id: int
    name: str
    size: int
    model_config = ConfigDict(from_attributes=True)


class CellBase(BaseModel):
    address: int
    path: str
    model_config = ConfigDict(from_attributes=True)

class StorageOut(StorageBaseOut):
    cells: List[CellBase] = Body([], description="Memory cells")
    model_config = ConfigDict(from_attributes=True)

class StorageList(BaseModel):
    storage_list: List[StorageBaseOut] = Body([], description="User storages")


class Upload_init_out(BaseModel):
    result: bool
    pk: int
    session: str


class Error(BaseModel):
    """Result of request processing"""

    result: bool = Body(
        ..., description="The status of processing", examples=[True]
    )
    error_type: str = Body(..., description="Error type")
    error_message: str = Body(..., description="Error message")


class Register(BaseModel):

    name: str
    api_key: str


class RegisterOut(BaseModel):
    result: bool