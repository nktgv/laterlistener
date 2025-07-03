from aiogram import Bot, Dispatcher
import asyncio
import os

from app.handlers import router


async def main():
    bot = Bot(token=' ') #ТОКЕН
    dp = Dispatcher()
    dp.include_router(router)
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')