from io import BytesIO

from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..config import SERVICE_BOT_USERNAME
from ..database import session as db
from ..models import Event, User
from ..service_bot.app import bot as service_bot
from ..states import ChatMode, PostCreate
from .app import bot, dp
from .markups import add_event, cancel_create_post_kb, cancel_operation, catalog, greetings_kb


@dp.message_handler(commands=["start"])
async def handle_greeting(message: Message) -> None:
    if len(message.text) > 7:
        post_id = message.text[11:]
        post = db.query(Event).filter(Event.id == post_id).first()
        await bot.send_photo(
            message.from_user.id,
            post.photo_id,
            caption=f'{post.name}' f'\n{post.title}' f'\n{post.description}',
            reply_markup=greetings_kb,
        )
    else:
        await message.answer(
            f"Добро пожаловать, {message.from_user.first_name} {message.from_user.last_name}!",
            reply_markup=greetings_kb
        )


@dp.message_handler(regexp=rf"^{add_event}$")
async def handle_create_post(message: Message) -> None:
    await PostCreate.post_name.set()
    await message.answer("Отправьте имя события", reply_markup=cancel_create_post_kb)


@dp.message_handler(regexp=rf"^{catalog}$")
async def handle_show_catalog(message: Message) -> None:
    for event in db.query(Event).limit(2).all():
        await bot.send_photo(
            message.from_user.id,
            event.photo_id,
            caption=f"{event.name}\n" f"\n{event.title}" f"\n{event.description}",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Удалить событие", callback_data=f"delete_{event.id}")
                if message.from_user.id == event.creator_id
                else InlineKeyboardButton("Связаться", callback_data=f"connect_{event.id}")
            ),
        )

    if db.query(Event).count() > 2:
        await message.answer(
            "Показать больше",
            reply_markup=InlineKeyboardMarkup().add(
                *[InlineKeyboardButton(f"[+{n}]", callback_data=f"see_more?c=2&n={n}") for n in {1, 5}]
            ),
        )


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

    button_connect_chat = InlineKeyboardButton(
        "Связаться", callback_data=f"connect_chat?c={data['client_id']}&e={data['event_id']}"
    )

    # TODO Ссылка на пост в маркапе
    button_check_event = InlineKeyboardButton(
        f"Посмотреть событие {data['event_name']}",
        url=f'https://t.me/InCst_test_bot?start=test{data["event_id"]}',
        callback_data=f"chat_check_event_{data['event_id']}",
    )
    markup_connect_chat = InlineKeyboardMarkup().add(button_connect_chat, button_check_event)

    try:
        user_status = db.query(User).filter(User.id == data["author_id"]).first().show_reply_markup
    except Exception:
        user_status = True

    if message.content_type == ContentType.TEXT:
        if message.text == "❌Выйти из чата":
            await state.finish()

            db.merge(User(id=message.from_user.id, show_reply_markup=True))
            db.commit()

            await bot.send_message(message.from_user.id, "Вы вышли из чата", reply_markup=greetings_kb)
        elif message.text == "Посмотреть событие":
            event = db.query(Event).filter(Event.id == data["event_id"]).first()

            await bot.send_photo(
                message.from_user.id,
                event.photo_id,
                caption=f"{event.name}\n\n{event.title}\n{event.description}",
            )
        elif message.text[:6] == "/start":
            await state.finish()

            db.merge(User(id=message.from_user.id, show_reply_markup=True))
            db.commit()

            await handle_greeting(message=message)
        else:
            await service_bot.send_message(
                data["author_id"],
                f"#Сообщение {data['event_name']}"
                f"\n{message.from_user.first_name} {message.from_user.last_name}: {message.text}",
                reply_markup=markup_connect_chat if user_status else None,
            )
    elif message.content_type == ContentType.PHOTO:
        await service_bot.send_photo(
            data["author_id"],
            await bot.download_file_by_id(message.photo[-1].file_id, destination=BytesIO()),
            caption=f"#Сообщение '{data['event_name']}'\n{message.from_user.first_name} {message.from_user.last_name}",
            reply_markup=(
                markup_connect_chat if db.query(User).filter(User.id == data["author_id"]).first().show_reply_markup else None
            ),
        )
    elif message.content_type == ContentType.VOICE:
        await service_bot.send_voice(
            data["author_id"],
            await bot.download_file_by_id(message.voice.file_id, destination=BytesIO()),
            caption=f"#Сообщение '{data['event_name']}'\n{message.from_user.first_name} {message.from_user.last_name}",
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.ANIMATION:
        await service_bot.send_animation(
            data["author_id"],
            await bot.download_file_by_id(message.animation.file_id, destination=BytesIO),
            caption=f"#Сообщение '{data['event_name']}'\n{message.from_user.first_name} {message.from_user.last_name}",
            width=512,
            height=512,
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.AUDIO:
        # TODO Добавить передачу названия аудио
        await service_bot.send_audio(
            data["author_id"],
            await bot.download_file_by_id(message.audio.file_id, destination=BytesIO()),
            caption=f"#Сообщение '{data['event_name']}'\n{message.from_user.first_name} {message.from_user.last_name}",
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.VIDEO:
        # TODO Добавить передачу названия видео
        await service_bot.send_video(
            data["author_id"],
            await bot.download_file_by_id(message.video.file_id, destination=BytesIO()),
            caption=f"#Сообщение '{data['event_name']}'\n{message.from_user.first_name} {message.from_user.last_name}",
            reply_markup=markup_connect_chat if user_status else None,
        )
    elif message.content_type == ContentType.STICKER:
        await service_bot.send_sticker(data["author_id"], message.sticker.file_id, reply_markup=markup_connect_chat if user_status else None)
    elif message.content_type == ContentType.LOCATION:
        await service_bot.send_location(
            data["author_id"], message.location.latitude, message.location.longitude,
            reply_markup=markup_connect_chat if user_status else None,
        )


@dp.message_handler(state=PostCreate.post_name)
async def create_post_step1(message: Message, state: FSMContext) -> None:
    if message.text == cancel_operation:
        await state.finish()
        await message.answer("Вы отменили создание события", reply_markup=greetings_kb)
    else:
        async with state.proxy() as data:
            data["post_name"] = message.text

        await PostCreate.next()
        await message.answer("Отправьте заголовок события", reply_markup=cancel_create_post_kb)


@dp.message_handler(state=PostCreate.post_title)
async def create_post_step2(message: Message, state: FSMContext) -> None:
    if message.text == cancel_operation:
        await state.finish()
        await message.answer("Вы отменили создание события", reply_markup=greetings_kb)
    else:
        await PostCreate.next()
        await state.update_data(post_title=message.text)
        await message.answer("Отправьте описание события", reply_markup=cancel_create_post_kb)


@dp.message_handler(state=PostCreate.post_description)
async def create_post_step3(message: Message, state: FSMContext) -> None:
    if message.text == cancel_operation:
        await state.finish()
        await message.answer("Вы отменили создание события", reply_markup=greetings_kb)
    else:
        await PostCreate.next()
        await state.update_data(post_description=message.text)
        await message.answer("Отправьте медиа (фото) для вашего обьявления", reply_markup=cancel_create_post_kb)


@dp.message_handler(content_types=["photo"], state=PostCreate.post_media)
async def create_post_step4(message: Message, state: FSMContext) -> None:
    if message.text == cancel_operation:
        await state.finish()
        await message.answer("Вы отменили создание события", reply_markup=greetings_kb)
    else:
        photo_id = message.photo[-1].file_id
        async with state.proxy() as data:
            data["post_media"] = str(photo_id)

        post_message = await bot.send_photo(
            message.from_user.id,
            photo_id,
            caption=f'{data["post_name"]}' f'\n{data["post_title"]}' f'\n{data["post_description"]}',
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Дата конца показа: ", callback_data="-")),
        )
        await bot.send_message(
            message.from_user.id,
            f"\nВы создали событие👆👆👆"
            f"\nДля того, чтобы получать уведомления о сообщениях перейдите в {SERVICE_BOT_USERNAME} и напишите /start",
            reply_markup=greetings_kb,
        )

        await state.finish()

        db.add(
            Event(
                name=data["post_name"],
                title=data["post_title"],
                description=data["post_description"],
                photo_id=data["post_media"],
                creator_id=message.from_user.id,
                message_id=post_message.message_id,
            )
        )
        db.commit()
