from typing import Optional, List
from pydantic import BaseModel, EmailStr
from sqlalchemy import ForeignKey
from sqlalchemy import Table, Column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


workspace_association = Table(
    "workspace_association",
    Base.metadata,
    Column("user_id", ForeignKey("user.id")),
    Column("workspace_id", ForeignKey("workspace.id")),
)


class User(Base):
    # noinspection SpellCheckingInspection
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(default=None, primary_key=True, unique=True, index=True)
    email: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    password: Mapped[str]
    is_activated: Mapped[bool]
    # We have not created Workspace yet, so we need to use "WorkSpace" in quotes
    workspaces: Mapped[Optional[List["Workspace"]]] = relationship(
        back_populates="users", secondary=workspace_association, cascade="all, delete")
    sessions: Mapped[Optional[List["Session"]]] = relationship(
        back_populates="session", cascade="all, delete")
    # FIXME: I CAN NOT UNDERSTAND HOW TO USE THIS FUCKING CASCADE
    last_active: Mapped[Optional[float]]


class Workspace(Base):
    # noinspection SpellCheckingInspection
    __tablename__ = "workspace"
    id: Mapped[int] = mapped_column(default=None, primary_key=True, unique=True, index=True)
    name: Mapped[str]
    owner_id: Mapped[int]
    users: Mapped[List[User]] = relationship(
        back_populates="workspaces", secondary=workspace_association, cascade="all, delete")


class Session(Base):
    # noinspection SpellCheckingInspection
    __tablename__ = "session"
    uuid: Mapped[str] = mapped_column(primary_key=True, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User] = relationship(back_populates="user")
    client_name: Mapped[str]
    ip: Mapped[str]
    last_active: Mapped[float]
    created_at: Mapped[float]


class Note(Base):
    # noinspection SpellCheckingInspection
    __tablename__ = "note"
    id: Mapped[int] = mapped_column(default=None, primary_key=True, unique=True, index=True)
    name: Mapped[str]
    owner_id: Mapped[int]
    is_in_workspace: Mapped[bool]
    has_children: Mapped[bool]
    path: Mapped[str] = mapped_column(index=True)
    real_path: Mapped[str]
    created_at: Mapped[float]
    last_edit_at: Mapped[float]


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class LogIn(BaseModel):
    username_or_email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    is_activated: bool
    last_active: float


class WorkSpaceOut(BaseModel):
    id: int
    name: str
    owner_id: int


class Token(BaseModel):
    access_token: str
    token_type: str
