from aiogram import Bot, Dispatcher
from aiogram.client.telegram import TelegramAPIServer 
from aiogram.client.session.aiohttp import AiohttpSession
import asyncio
import os
import aiofiles.os
from dotenv import load_dotenv

from app.handlers import router


async def main():
    load_dotenv()
    token = os.environ.get('BOT_TOKEN')
    if not token:
        raise ValueError('Переменная окружения BOT_TOKEN не задана!')
    session = AiohttpSession(api=TelegramAPIServer.from_base("http://localhost:8081", is_local=True))
    bot = Bot(token=token, session=session) #ТОКЕН
    dp = Dispatcher()
    dp.include_router(router)
    if not os.path.exists("downloads"):
        await aiofiles.os.makedirs("downloads")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
