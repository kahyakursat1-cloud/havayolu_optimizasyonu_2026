import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Ensure project root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.db.models import User, Base
from src.db.config import async_session_maker, UserManager
from src.db.schemas import UserCreate
from fastapi_users.db import SQLAlchemyUserDatabase

async def seed_user():
    print("Checking for test user...")
    async with async_session_maker() as session:
        res = await session.execute(select(User).where(User.email == "test@skylogic.com"))
        user = res.scalars().first()
        
        if user:
            print(f"✅ User test@skylogic.com already exists (ID: {user.id})")
            return
        
        print("Creating test user...")
        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)
        
        user_create = UserCreate(
            email="test@skylogic.com",
            password="Skylogic123!",
            is_active=True,
            is_superuser=True,
            is_verified=True
        )
        created_user = await user_manager.create(user_create)
        print(f"✅ User test@skylogic.com created successfully (ID: {created_user.id})")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_user())
