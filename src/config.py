import os

from aiogram.contrib.fsm_storage.memory import MemoryStorage

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

storage = MemoryStorage()

CLIENT_BOT_TOKEN = os.getenv("CLIENT_BOT_TOKEN")

SERVICE_BOT_TOKEN = os.getenv("SERVICE_BOT_TOKEN")
SERVICE_BOT_USERNAME = os.getenv("SERVICE_BOT_USERNAME")
