from io import BytesIO

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

from ..client_bot.app import bot as client_bot
from ..database import session as db
from ..models import User
from ..states import ChatMode
from .app import bot, dp


@dp.message_handler(
    state=ChatMode.chat_mode,
    content_types=[
        ContentType.LOCATION,
        ContentType.STICKER,
        ContentType.PHOTO,
        ContentType.TEXT,
        ContentType.VOICE,
        ContentType.ANIMATION,
        ContentType.AUDIO,
        ContentType.VIDEO,
    ],
)
async def post_chat_mode(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["client_id"] = message.from_user.id

    markup_connect_chat = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Связаться", callback_data=f"connect_{data['event_id']}"),
        InlineKeyboardButton(
            f"Посмотреть событие {data['event_name']}", callback_data=f"chat_check_event{data['event_id']}"
        ),
    )

    try:
        user_status = db.query(User).filter(User.id == data["customer_id"]).first().show_reply_markup
    except Exception:
        user_status = True

    if message.content_type == ContentType.TEXT:
        if message.text == "❌Выйти из чата":
            await state.finish()

            db.merge(User(id=message.from_user.id, show_reply_markup=True))
            db.commit()

            await bot.send_message(message.from_user.id, "Вы вышли из чата", reply_markup=ReplyKeyboardRemove())
        else:
            await client_bot.send_message(
                data["customer_id"],
                f"Сообщение от владельца события '{data['event_name']}'\n{message.text}",
                reply_markup=markup_connect_chat if user_status else None,
            )
    elif message.content_type == ContentType.PHOTO:
        await client_bot.send_photo(
            data["customer_id"],
            await bot.download_file_by_id(message.photo[-1].file_id, destination=BytesIO()),
            caption=f"Сообщение от владельца события '{data['event_name']}'",
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.VOICE:
        await client_bot.send_voice(
            data["customer_id"],
            await bot.download_file_by_id(message.voice.file_id, destination=BytesIO()),
            caption=f"Сообщение от владельца события '{data['event_name']}'",
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.ANIMATION:
        await client_bot.send_animation(
            data["customer_id"],
            await bot.download_file_by_id(message.animation.file_id, destination=BytesIO()),
            caption=f"Сообщение от владельца события '{data['event_name']}'",
            width=512,
            height=512,
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.AUDIO:
        # TODO Добавить передачу названия аудио
        await client_bot.send_audio(
            data["customer_id"],
            await bot.download_file_by_id(message.audio.file_id, destination=BytesIO()),
            caption=f"Сообщение от владельца события '{data['event_name']}'",
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.VIDEO:
        # TODO Добавить передачу названия видео
        await client_bot.send_video(
            data["customer_id"],
            await bot.download_file_by_id(message.video.file_id, destination=BytesIO()),
            caption=f"Сообщение от владельца события '{data['event_name']}'",
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.STICKER:
        await client_bot.send_sticker(data["customer_id"], message.sticker.file_id,
                                      reply_markup=markup_connect_chat if user_status else None)
    elif message.content_type == ContentType.LOCATION:
        await client_bot.send_location(
            data["customer_id"], message.location.latitude, message.location.longitude,
            reply_markup=markup_connect_chat if user_status else None,
        )
