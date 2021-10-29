from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

catalog = "Каталог"
button_catalog = KeyboardButton(catalog)
add_event = "Добавить событие"
button_create_post = KeyboardButton(add_event)
greetings_kb = ReplyKeyboardMarkup(resize_keyboard=True)
greetings_kb.add(button_catalog, button_create_post)

cancel_operation = "Отменить операцию"
button_cancel_create_post = KeyboardButton(cancel_operation)
cancel_create_post_kb = ReplyKeyboardMarkup(resize_keyboard=True)
cancel_create_post_kb.add(button_cancel_create_post)
