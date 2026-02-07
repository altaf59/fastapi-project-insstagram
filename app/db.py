from collections.abc import AsyncGenerator
from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
from fastapi_users.db import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID
from fastapi import Depends

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

Base = declarative_base()

# User table
class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"
    posts = relationship("Post", back_populates="user")

# Post table
class Post(Base):
    __tablename__ = "post"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(GUID, ForeignKey("user.id"), nullable=False)
    caption = Column(Text)
    url = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="posts")

# Database engine
engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Create tables
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Async session
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# FastAPI Users DB
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
