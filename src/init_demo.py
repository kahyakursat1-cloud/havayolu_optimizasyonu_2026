import asyncio
import uuid
from src.db.config import async_session_maker, db_engine as engine
from src.db.models import Base, User
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

async def create_demo_user():
    print("Checking for demo user...")
    from fastapi_users.password import PasswordHelper
    
    password_helper = PasswordHelper()
    hashed_password = password_helper.hash("password123")
    
    async with async_session_maker() as session:
        # Check if user exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "admin@skylogic.com"))
        if result.scalar_one_or_none():
            print("Demo user already exists.")
            return

        user = User(
            id=uuid.uuid4(),
            email="admin@skylogic.com",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
            is_verified=True,
            full_name="Admin Operator",
            role="admin"
        )
        session.add(user)
        await session.commit()
        print("Demo user created: admin@skylogic.com / password123")

async def main():
    # In Phase 2, we assume migrations are run via Alembic, 
    # but we'll ensure the demo user is present.
    await create_demo_user()

if __name__ == "__main__":
    asyncio.run(main())
