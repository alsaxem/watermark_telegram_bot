import pickle
from telebot import types
import wmbed
import telebot
import os
from keyboa import Keyboa
from config import (
    token,
    temp_file_path,
    photos_path,
    save_path,
    position_values,
    scale_values,
    opacity_values,
    users_file_path,
)

amogus = {}

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    text = "Добро пожаловать.\nБот поможет вам защитить изображение водяным знаком для подтверждения авторства."
    amogus[message.chat.id] = {
        "watermark_id": 0,
        "position": 0,
        "scale": 0,
        "opacity": 0,
        "padding": 0}
    bot.send_message(chat_id=message.chat.id, text=text)
    save_dict()
    request_watermark_photo(message)


def request_watermark_photo(message):
    text = "Отправьте водяной знак для ваших будущих фото. Обычно это адрес сайта, логотип компании или контакт " \
           "автора, но вы можете использовать любое изображение."
    bot.send_message(chat_id=message.chat.id, text=text)
    bot.register_next_step_handler(message, set_watermark_photo)


def request_watermark_position(message):
    text = "Выберете место расположения водяного знака:"
    keyboard = Keyboa(items=position_values, items_in_row=2)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_scale(message):
    text = "Выберете множитель размера водяного знака:"
    keyboard = Keyboa(items=scale_values, items_in_row=5)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_opacity(message):
    text = "Выберете прозрачность водяного знака:"
    keyboard = Keyboa(items=opacity_values, items_in_row=5)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_padding(message):
    text = "Укажите отступ водяного знака от края изображения в пикселях:"
    bot.send_message(chat_id=message.chat.id, text=text)
    bot.register_next_step_handler(message, set_padding)


def set_watermark_photo(message):
    try:
        photo_number = len(message.photo) - 1
        amogus[message.chat.id]["watermark_id"] = message.photo[photo_number].file_id
        text = "Знак добавлен"
        bot.send_message(chat_id=message.chat.id, text=text)
        save_dict()
        add_parameters(message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуй еще раз."
        bot.send_message(chat_id=message.chat.id, text=text)
        bot.register_next_step_handler(message, request_opacity)


def set_position(call):
    try:
        amogus[call.message.chat.id]["position"] = call.data
        save_dict()
        add_parameters(call.message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуй еще раз."
        if amogus[call.message.chat.id]["watermark_id"] == 0:
            text = "Сначала необходимо отправить водяной знак"
        bot.send_message(chat_id=call.message.chat.id, text=text)
        bot.register_next_step_handler(call.message, request_watermark_position)


def set_scale(call):
    try:
        amogus[call.message.chat.id]["scale"] = float(call.data[1:])
        save_dict()
        add_parameters(call.message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуй еще раз."
        bot.send_message(chat_id=call.message.chat.id, text=text)
        bot.register_next_step_handler(call.message, request_scale)


def set_opacity(call):
    try:
        amogus[call.message.chat.id]["opacity"] = float(call.data)
        save_dict()
        add_parameters(call.message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуй еще раз."
        bot.send_message(chat_id=call.message.chat.id, text=text)
        bot.register_next_step_handler(call.message, request_opacity)


def set_padding(message):
    if message.text.isdigit():
        amogus[message.chat.id]["padding"] = int(message.text)
        bot.send_message(message.chat.id, "Сохранен отступ в " + message.text + " пикселей")
        save_dict()
        add_parameters(message)
    else:
        bot.send_message(message.chat.id, "Отступ необходимо указывать в виде целого числа! Попробуй еще раз.")
        bot.register_next_step_handler(message, request_padding)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline_position(call):
    if call.data in position_values:
        set_position(call)
    elif call.data in scale_values:
        set_scale(call)
    elif call.data in opacity_values:
        set_opacity(call)


def get_reply_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = types.KeyboardButton('Мои настройки')
    button2 = types.KeyboardButton('Изменить настройки')
    keyboard.add(button1, button2)
    return keyboard


def process_photo(photo_path, watermark_path, user_id):
    wmbed.create_marked_image(
        image_path=photo_path,
        watermark_path=watermark_path,
        save_path=save_path,
        position=amogus[user_id]["position"],
        scale=amogus[user_id]["scale"],
        opacity=amogus[user_id]["opacity"],
        padding=amogus[user_id]["padding"]
    )


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.chat.id not in amogus:
        start(message)
    elif 0 in amogus[message.chat.id]:
        add_parameters(message)
    elif message.text == "Мои настройки":
        send_settings(message.chat.id)
    elif message.text == 'Изменить настройки':
        pass
    else:
        text = "Отправь фото для наложения водяного знака"
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard())


def send_settings(user_id):
    settings = ""
    for setting_name, setting_value in amogus[user_id].items():
        if setting_name != "watermark_id":
            settings += f"{setting_name}: {setting_value}\n"
    bot.send_message(chat_id=user_id, text=settings)


def add_parameters(message):
    if amogus[message.chat.id]["watermark_id"] == 0:
        request_watermark_photo(message)
    elif amogus[message.chat.id]["position"] == 0:
        request_watermark_position(message)
    elif amogus[message.chat.id]["scale"] == 0:
        request_scale(message)
    elif amogus[message.chat.id]["opacity"] == 0:
        request_opacity(message)
    elif amogus[message.chat.id]["padding"] == 0:
        request_padding(message)
    else:
        text = "Все параметры указаны. Отправь фото, которое хочешь защитить"
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard())


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    if message.chat.id not in amogus:
        start(message)
    elif 0 in amogus[message.chat.id].values():
        add_parameters(message)
    else:
        try:
            watermark_path = download_photo(amogus[message.chat.id]["watermark_id"])
            photo_path = download_photo(message.photo[len(message.photo) - 1].file_id)
            process_photo(photo_path, watermark_path, message.chat.id)
            bot.send_photo(message.chat.id, open(save_path, 'rb'))
            delete_file()
        except Exception as e:
            bot.reply_to(message, str(e))


def download_photo(file_id):
    file_info = bot.get_file(file_id=file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    photo_path = temp_file_path + file_info.file_path
    with open(photo_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    return photo_path


def delete_file():
    folder_path = temp_file_path + "photos"
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def save_dict():
    with open(users_file_path, 'wb') as f:
        pickle.dump(amogus, f)


if os.path.exists(users_file_path):
    with open(users_file_path, 'rb') as f:
        amogus = pickle.load(f)

if not os.path.exists(temp_file_path):
    os.makedirs(temp_file_path)

if not os.path.exists(os.path.join(temp_file_path, photos_path)):
    os.makedirs(os.path.join(temp_file_path, photos_path))


for user_id, user_data in amogus.items():
    try:
        message_text = 'Привет, я снова работаю!'
        bot.send_message(chat_id=user_id, text=message_text, reply_markup=get_reply_keyboard())
    except Exception as a:
        print(f'Не удалось отправить сообщение пользователю {user_id} (user_data: {user_data})')

bot.polling(none_stop=True)
