import re

from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from ..database import session as db
from ..models import Event, User
from ..service_bot.app import bot as service_bot
from ..states import ChatMode
from .app import bot, dp
from .markups import greetings_kb


@dp.callback_query_handler(lambda c: c.data[:8] == "see_more", state=ChatMode.chat_mode)
@dp.callback_query_handler(lambda c: c.data[:8] == "see_more")
async def handle_see_more(callback_query: CallbackQuery) -> None:
    await bot.answer_callback_query(callback_query.id)

    current_count, next_count = re.match(r"^see_more\?c=(\d+)&n=(\d+)$", callback_query.data).groups()
    post_count = int(current_count) + int(next_count)

    for event in db.query(Event).limit(post_count).all():
        await bot.send_photo(
            callback_query.from_user.id,
            event.photo_id,
            caption=f"{event.name}\n" f"\n{event.title}" f"\n{event.description}",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Удалить событие", callback_data=f"delete_{event.id}")
                if callback_query.from_user.id == event.creator_id
                else InlineKeyboardButton("Связаться", callback_data=f"connect_{event.id}")
            ),
        )

    if db.query(Event).count() > post_count:
        await bot.send_message(
            callback_query.from_user.id,
            "Показать больше",
            reply_markup=InlineKeyboardMarkup().add(
                *[InlineKeyboardButton(f"[+{n}]", callback_data=f"see_more?c={post_count}&n={n}") for n in {1, 5}]
            ),
        )
        await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)


@dp.callback_query_handler(lambda c: c.data[:7] == "connect", state=ChatMode.chat_mode)
@dp.callback_query_handler(lambda c: c.data[:7] == "connect")
async def process_enter_chat(callback_query: CallbackQuery, state: FSMContext) -> None:
    await ChatMode.chat_mode.set()

    db.merge(User(id=callback_query.from_user.id, show_reply_markup=False))
    db.commit()

    post_id = callback_query.data[8:]
    event = db.query(Event).filter(Event.id == post_id).first()

    async with state.proxy() as data:
        data["event_id"] = post_id
        data["msg_id"] = event.message_id
        data["author_id"] = event.creator_id
        data["event_name"] = event.title
        data["chat_id"] = callback_query.message.chat.id

    await bot.send_message(
        callback_query.from_user.id,
        f"Вы вошли в режим чата с владельцем обьявления {event.title}.",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("❌Выйти из чата", callback_data=f"leave_chat"),
            KeyboardButton("Посмотреть событие", callback_data=f"chat_check_event_{post_id}"),
        ),
    )
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data[:16] == "chat_check_event")
async def process_chat_check_event(callback_query: CallbackQuery) -> None:
    post_id = callback_query.data[17:]
    event = db.query(Event).filter(Event.id == post_id).first()

    await service_bot.send_photo(
        callback_query.from_user.id, event.photo_id, caption=f"{event.name}\n\n{event.title}\n{event.description}"
    )
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data[:6] == "delete", state=ChatMode.chat_mode)
@dp.callback_query_handler(lambda c: c.data[:6] == "delete")
async def process_callback_delete(callback_query: CallbackQuery) -> None:
    await bot.send_message(
        callback_query.from_user.id,
        "Вы точно хотите удалить это обьявление?",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("Да", callback_data=f"confirm_{callback_query.data}"),
            InlineKeyboardButton("Нет", callback_data=f"cancel_{callback_query.data}"),
        ),
    )
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data[:14] == "confirm_delete", state=ChatMode.chat_mode)
@dp.callback_query_handler(lambda c: c.data[:14] == "confirm_delete")
async def process_callback_cm_delete(callback_query: CallbackQuery) -> None:
    event_id = re.match(r"^confirm_delete_(\d+)$", callback_query.data).group(1)
    db.query(Event).filter(Event.id == event_id).delete()

    await bot.send_message(callback_query.from_user.id, "Вы успешно удалили обьявление! Обновите каталог.")
    await bot.answer_callback_query(callback_query.id)


@dp.callback_query_handler(lambda c: c.data[:13] == "cancel_delete", state=ChatMode.chat_mode)
@dp.callback_query_handler(lambda c: c.data[:13] == "cancel_delete")
async def process_callback_cl_delete(callback_query: CallbackQuery) -> None:
    await bot.send_message(
        callback_query.from_user.id,
        "Вы отменили удаление обьявления! Cпасибо, что остаетесь с нами!",
        reply_markup=greetings_kb,
    )
    await bot.answer_callback_query(callback_query.id)
