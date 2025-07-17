# import aiosqlite
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv
import os



load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(url, key)


































































# DB_PATH = "users.db"

# async def init_db():
#     async with aiosqlite.connect(DB_PATH) as db:
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS users (
#             user_id INTEGER PRIMARY KEY,
#             balance INTEGER DEFAULT 0
#         )
#         """)
#         await db.commit()

# async def select_user(user_id: int):
#     async with aiosqlite.connect(DB_PATH) as db:
#         cursor = await db.execute("SELECT user_id, balance FROM users WHERE user_id = ?", (user_id,))
#         return await cursor.fetchone()

# async def add_user_if_not_exists(user_id: int):
#     if not await select_user(user_id):
#         async with aiosqlite.connect(DB_PATH) as db:
#             await db.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
#             await db.commit()

# async def update_balance(user_id: int, amount: int):
#     await add_user_if_not_exists(user_id)
#     async with aiosqlite.connect(DB_PATH) as db:
#         await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
#         await db.commit()

# async def get_balance(user_id: int):
#     await add_user_if_not_exists(user_id)
#     async with aiosqlite.connect(DB_PATH) as db:
#         cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
#         row = await cursor.fetchone()
#         return row[0] if row else 0

# async def add_user(user_id: int):
#     """Псевдоним для add_user_if_not_exists, для читаемости в balance.py"""
#     await add_user_if_not_exists(user_id)

# async def add_balance(user_id: int, amount: int):
#     """Добавление указанного количества к балансу пользователя."""
#     await update_balance(user_id, amount)
