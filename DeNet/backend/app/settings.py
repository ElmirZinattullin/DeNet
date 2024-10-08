from pydantic_settings import BaseSettings
from pydantic_core import ValidationError
from pydantic import Field


class APISettings(BaseSettings):
    database: str
    database_user: str
    database_password: str
    debug: bool = False
    database_url: str

try:
    Settings = APISettings().model_dump()
except ValidationError:
    raise Exception("NO FOUND ONE OR MORE ENVIRONMENTS")

DATABASE = Settings.get("database")
DATABASE_USER = Settings.get("database_user")
DATABASE_PASSWORD = Settings.get("database_password")
DEBUG = Settings.get("debug")
DATABASE_URL = Settings.get("database_url")
