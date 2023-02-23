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
    empty_value,
    settings,
    position_values,
    scale_values,
    opacity_values,
    padding_values,
    users_file_path,
)

amogus = {}

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    text = "Добро пожаловать.\nБот поможет вам защитить изображение водяным знаком."
    amogus[message.chat.id] = {
        "watermark_id": empty_value,
        "position": empty_value,
        "scale": empty_value,
        "opacity": empty_value,
        "padding": empty_value}
    bot.send_message(chat_id=message.chat.id, text=text)
    save_dict()
    request_watermark_photo(message)


def request_watermark_photo(message):
    text = "Отправьте водяной знак для ваших будущих фото. Вы можете использовать любое изображение."
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
    text = "Укажите отступ водяного знака от края изображения в процентах:"
    keyboard = Keyboa(items=padding_values, items_in_row=5)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


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
        text = "Что-то пошло не так. Попробуйте еще раз."
        bot.send_message(chat_id=message.chat.id, text=text)
        bot.register_next_step_handler(message, request_opacity)


@bot.callback_query_handler(func=lambda call: call.data in position_values)
def set_position(call):
    try:
        amogus[call.message.chat.id]["position"] = call.data
        save_dict()
        add_parameters(call.message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуйте еще раз."
        bot.send_message(chat_id=call.message.chat.id, text=text)
        bot.register_next_step_handler(call.message, request_watermark_position)


@bot.callback_query_handler(func=lambda call: call.data in scale_values)
def set_scale(call):
    try:
        amogus[call.message.chat.id]["scale"] = float(call.data[1:])
        save_dict()
        add_parameters(call.message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуйте еще раз."
        bot.send_message(chat_id=call.message.chat.id, text=text)
        bot.register_next_step_handler(call.message, request_scale)


@bot.callback_query_handler(func=lambda call: call.data in opacity_values)
def set_opacity(call):
    try:
        amogus[call.message.chat.id]["opacity"] = float(call.data)
        save_dict()
        add_parameters(call.message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуйте еще раз."
        bot.send_message(chat_id=call.message.chat.id, text=text)
        bot.register_next_step_handler(call.message, request_opacity)


@bot.callback_query_handler(func=lambda call: call.data in padding_values)
def set_padding(call):
    try:
        amogus[call.message.chat.id]["padding"] = float(call.data[:-1]) / 100
        save_dict()
        add_parameters(call.message)
    except Exception as e:
        print(e)
        text = "Что-то пошло не так. Попробуйте еще раз."
        bot.send_message(chat_id=call.message.chat.id, text=text)
        bot.register_next_step_handler(call.message, request_padding)


def get_reply_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = types.KeyboardButton('Мои настройки')
    button2 = types.KeyboardButton('Изменить настройки')
    keyboard.add(button1, button2)
    return keyboard


def process_photo(photo_path, watermark_path, user_id):
    wmbed.create_image_with_positional_watermark(
        image_path=photo_path,
        watermark_path=watermark_path,
        save_path=save_path,
        position=amogus[user_id]["position"],
        scale=amogus[user_id]["scale"],
        opacity=amogus[user_id]["opacity"],
        relative_padding=amogus[user_id]["padding"]
    )


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.chat.id not in amogus:
        start(message)
    elif empty_value in amogus[message.chat.id]:
        add_parameters(message)
    elif message.text == "Мои настройки":
        send_settings(message.chat.id)
    elif message.text == 'Изменить настройки':
        request_change_setting(message.chat.id)
    else:
        text = "Отправьте фото для наложения водяного знака."
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard())


def send_settings(user_id):
    user_settings = ""
    for setting_name, setting_value in amogus[user_id].items():
        if setting_name != "watermark_id":
            user_settings += f"{setting_name}: {setting_value}\n"
    bot.send_message(chat_id=user_id, text=user_settings)


def request_change_setting(user_id):
    text = "Выберете параметр, который вы хотите изменить:"
    keyboard = Keyboa(items=settings, items_in_row=1)
    bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard())


@bot.callback_query_handler(func=lambda call: call.data in settings)
def change_setting(call):
    amogus[call.message.chat.id][call.data] = empty_value
    add_parameters(call.message)


def add_parameters(message):
    if amogus[message.chat.id]["watermark_id"] == empty_value:
        request_watermark_photo(message)
    elif amogus[message.chat.id]["position"] == empty_value:
        request_watermark_position(message)
    elif amogus[message.chat.id]["scale"] == empty_value:
        request_scale(message)
    elif amogus[message.chat.id]["opacity"] == empty_value:
        request_opacity(message)
    elif amogus[message.chat.id]["padding"] == empty_value:
        request_padding(message)
    else:
        text = "Все параметры указаны. Отправьте фото, которое хочешь защитить"
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard())


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    if message.chat.id not in amogus:
        start(message)
    elif empty_value in amogus[message.chat.id].values():
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


def load_dict():
    global amogus
    if os.path.exists(users_file_path):
        with open(users_file_path, 'rb') as f:
            amogus = pickle.load(f)


def check_directories():
    if not os.path.exists(temp_file_path):
        os.makedirs(temp_file_path)
    if not os.path.exists(os.path.join(temp_file_path, photos_path)):
        os.makedirs(os.path.join(temp_file_path, photos_path))


def send_start_message(text='Привет, я снова работаю!'):
    for user_id, user_data in amogus.items():
        try:
            bot.send_message(chat_id=user_id, text=text, reply_markup=get_reply_keyboard())
        except Exception as a:
            print(f'Не удалось отправить сообщение пользователю {user_id} (user_data: {user_data})')


def bot_launch():
    load_dict()
    check_directories()
    send_start_message()


bot_launch()
bot.polling(none_stop=True)
