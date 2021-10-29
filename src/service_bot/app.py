import asyncio

from aiogram import Bot, Dispatcher
from src.config import SERVICE_BOT_TOKEN, storage

bot = Bot(token=SERVICE_BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)


async def run() -> None:
    await dp.start_polling()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
