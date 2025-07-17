# fake_database.py — файл-заглушка вместо database.py

_users = {}  # словарь user_id: balance

async def get_balance(user_id: int):
    return _users.get(user_id, 0)

async def add_user(user_id: int):
    _users.setdefault(user_id, 0)

async def add_balance(user_id: int, amount: int):
    _users[user_id] = _users.get(user_id, 0) + amount
