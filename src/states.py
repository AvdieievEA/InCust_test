from aiogram.dispatcher.filters.state import State, StatesGroup


class PostCreate(StatesGroup):
    post_name = State()
    post_title = State()
    post_description = State()
    post_media = State()


class ChatMode(StatesGroup):
    chat_mode = State()
