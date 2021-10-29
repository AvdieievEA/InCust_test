import asyncio

from src.client_bot.app import run as run_client
from src.service_bot.app import run as run_service


async def run() -> None:
    await asyncio.gather(run_client(), run_service())


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(run())
