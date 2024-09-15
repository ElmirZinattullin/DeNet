from typing import Any, Dict, List

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
    select,
    Integer,
    Uuid
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base



class Cell(AsyncAttrs, Base):
    __tablename__ = "cells"
    __table_args__ = UniqueConstraint(
        "address", "storage_id"
    ), UniqueConstraint("path")
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String())
    address: Mapped[int] = mapped_column(Integer(), default=0)
    storage_id: Mapped["int"] = mapped_column(
        ForeignKey("storage.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    storage: Mapped["Storage"] = relationship(lazy="joined", back_populates="cells")


class Storage(AsyncAttrs, Base):
    __tablename__ = "storage"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    size: Mapped[int] = mapped_column(Integer())
    user_id: Mapped["int"] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(lazy="joined", back_populates="storage_list")
    cells: Mapped[List["Cell"]] = relationship(lazy="joined", back_populates="storage")


class User(AsyncAttrs, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    api_key: Mapped[str]
    storage_list: Mapped[List["Storage"]] = relationship(lazy="joined", back_populates="user")


class UploadSession(AsyncAttrs, Base):
    __tablename__ = "uploadsessions"
    session: Mapped[str] = mapped_column(Uuid(), primary_key=True)
    storage_id: Mapped[int] = mapped_column(
        ForeignKey("storage.id", onupdate="CASCADE", ondelete="CASCADE")
    )
    storage: Mapped["Storage"] = relationship("Storage", lazy="joined")