import asyncio
from sqlalchemy import select
from app.db import engine, Post, User, create_db_and_tables

async def check():
    await create_db_and_tables()
    async with engine.connect() as conn:
        # Check Posts
        res = await conn.execute(select(Post))
        posts = res.all()
        print(f"Total Posts in DB: {len(posts)}")
        for p in posts:
            print(f"Post ID: {p.id}, User ID: {p.user_id}")
            
        # Check Users
        res = await conn.execute(select(User))
        users = res.all()
        print(f"Total Users in DB: {len(users)}")
        for u in users:
            print(f"User ID: {u.id}, Email: {u.email}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
