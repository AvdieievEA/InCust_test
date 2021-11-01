import re

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, ReplyKeyboardMarkup

from ..database import session as db
from ..models import Event, User
from ..states import ChatMode
from .app import bot, dp


@dp.callback_query_handler(lambda c: c.data[:12] == "connect_chat", state=ChatMode.chat_mode)
@dp.callback_query_handler(lambda c: c.data[:12] == "connect_chat")
async def process_enter_chat(callback_query: CallbackQuery, state: FSMContext) -> None:
    customer_id, event_id = re.match(r"^connect_chat\?c=(\d*)&e=(\d+)$", callback_query.data).groups()

    await ChatMode.chat_mode.set()

    db.merge(User(id=callback_query.from_user.id, show_reply_markup=False))
    db.commit()

    event = db.query(Event).filter(Event.id == event_id).first()

    async with state.proxy() as data:
        data["event_id"] = event_id
        data["msg_id"] = event.message_id
        data["author_id"] = event.creator_id
        data["event_name"] = event.title
        data["chat_id"] = callback_query.message.chat.id
        data["customer_id"] = customer_id

    await bot.send_message(
        data["author_id"],
        f"Вы вошли в режим чата' {event.title}.",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("❌Выйти из чата", callback_data=f"leave_chat"),
        ),
    )
    await bot.answer_callback_query(callback_query.id)