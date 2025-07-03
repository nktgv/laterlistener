from aiogram import Bot, Dispatcher
import asyncio
import os
from dotenv import load_dotenv

from app.handlers import router


async def main():
    load_dotenv()
    token = os.environ.get('BOT_TOKEN')
    if not token:
        raise ValueError('Переменная окружения BOT_TOKEN не задана!')
    bot = Bot(token=token) #ТОКЕН
    dp = Dispatcher()
    dp.include_router(router)
    if not os.path.exists("downloads"):
        os.makedirs("bot/downloads")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')