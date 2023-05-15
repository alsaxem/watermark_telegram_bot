from wmbed.telegram_api import *
import telebot
from keyboa import Keyboa
from config import *
from bot_token import *
import dbutils

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    text = "Добро пожаловать.\nБот поможет вам защитить изображение водяным знаком."
    dbutils.add_user(message.chat.id, message.from_user.first_name + " " + message.from_user.last_name)
    bot.send_message(chat_id=message.chat.id, text=text)
    request_watermark_photo(message)


@bot.message_handler(commands=['sendall'])
def sendall(message):
    if message.chat.id == owner_id:
        send_to_all(message.text.replace("/sendall", ""))


def request_watermark_photo(message):
    text = "Отправьте водяной знак для ваших будущих фото. Вы можете использовать любое изображение."
    bot.send_message(chat_id=message.chat.id, text=text)
    bot.register_next_step_handler(message, set_watermark_photo)


def request_watermark_position(message):
    text = "Выберете место расположения водяного знака:"
    keyboard = Keyboa(items=position_values, items_in_row=3)
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


def request_angle(message):
    text = "Укажите угол поворота водяного знака (целое число):"
    bot.send_message(chat_id=message.chat.id, text=text)
    bot.register_next_step_handler(message, set_angle)


def set_watermark_photo(message):
    try:
        photo_id = get_photo_id(message)
        if photo_id != empty_value:
            dbutils.update_info(message.chat.id, "watermark_id", photo_id)
            text = "Знак добавлен"
            bot.send_message(chat_id=message.chat.id, text=text)
        else:
            text = "Водяным знаком может быть только фото!"
            bot.send_message(chat_id=message.chat.id, text=text)
        add_parameters(message)
    except Exception as e:
        print("ERROR: set_watermark_photo")
        print(e)
        process_exception(message)
        bot.register_next_step_handler(message, request_watermark_photo)


@bot.callback_query_handler(func=lambda call: call.data in position_values)
def set_position(call):
    try:
        set_parameter(call.message, column="position", data=call.data)
    except Exception as e:
        print("ERROR: set_position")
        print(e)
        process_exception(call.message)
        bot.register_next_step_handler(call.message, request_watermark_position)


@bot.callback_query_handler(func=lambda call: call.data in scale_values)
def set_scale(call):
    try:
        set_parameter(call.message, column="scale", data=float(call.data[1:]))
    except Exception as e:
        print("ERROR: set_scale")
        print(e)
        process_exception(call.message)
        bot.register_next_step_handler(call.message, request_scale)


@bot.callback_query_handler(func=lambda call: call.data in opacity_values)
def set_opacity(call):
    try:
        set_parameter(call.message, column="opacity", data=float(call.data))
    except Exception as e:
        print("ERROR: set_opacity")
        print(e)
        process_exception(call.message)
        bot.register_next_step_handler(call.message, request_opacity)


@bot.callback_query_handler(func=lambda call: call.data in padding_values)
def set_padding(call):
    try:
        set_parameter(call.message, column="padding", data=float(call.data[:-1]) / 100)
    except Exception as e:
        print("ERROR: set_padding")
        print(e)
        process_exception(call.message)
        bot.register_next_step_handler(call.message, request_padding)


def set_angle(message):
    try:
        set_parameter(message, column="angle", data=int(message.text), is_remove=False)
    except Exception as e:
        print("ERROR: set_angle")
        print(e)
        process_exception(message)
        bot.register_next_step_handler(message, request_angle)


def set_parameter(message, column, data, is_remove=True):
    if is_remove:
        bot.delete_message(message.chat.id, message.message_id)
    dbutils.update_info(message.chat.id, column, data)
    add_parameters(message)


def process_exception(message):
    text = "Что-то пошло не так. Попробуйте еще раз."
    bot.send_message(chat_id=message.chat.id, text=text)


def get_reply_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button1 = telebot.types.KeyboardButton('Мои настройки')
    button2 = telebot.types.KeyboardButton('Изменить настройки')
    keyboard.add(button1, button2)
    return keyboard


def process_photo(photo_bytearray, watermark_bytearray, user_id):
    position, scale, opacity, padding, angle = dbutils.get_fields_info(user_id,
                                                                       "position, scale, opacity, padding, angle")
    if position == "FILLING":
        photo_bytearray = create_image_with_watermark_tiling(
            image_bytearray=photo_bytearray,
            watermark_bytearray=watermark_bytearray,
            scale=scale,
            angle=angle,
            opacity=opacity,
        )
    else:
        photo_bytearray = create_image_with_positional_watermark(
            image_bytearray=photo_bytearray,
            watermark_bytearray=watermark_bytearray,
            position=position,
            scale=scale,
            angle=angle,
            opacity=opacity,
            relative_padding=padding,
        )
    return photo_bytearray


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "Мои настройки":
        send_settings(message.chat.id)
    elif message.text == 'Изменить настройки':
        request_change_setting(message.chat.id)
    elif check_settings(message):
        text = "Отправьте фото для наложения водяного знака."
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard())


def check_settings(message):
    user_data = dbutils.get_fields_info(message.chat.id, "watermark_id, position, scale, opacity, angle, padding")
    if not dbutils.is_user_exist(message.chat.id):
        start(message)
    elif empty_value in user_data[:-1] or \
            user_data[1] != "FILLING" and user_data[-1] == empty_value:
        add_parameters(message)
    else:
        return True
    return False


def send_settings(user_id):
    user_settings = ""
    setting_names = ["position", "scale", "opacity", "angle", "padding"]
    setting_values = dbutils.get_fields_info(user_id, "position, scale, opacity, angle, padding")
    if not setting_values:
        setting_values = [empty_value, empty_value, empty_value, empty_value, empty_value]
    for i in range(0, len(setting_names)):
        user_settings += f"{setting_names[i]}: {setting_values[i]}\n"
    bot.send_message(chat_id=user_id, text=user_settings)


def request_change_setting(user_id):
    text = "Выберете параметр, который вы хотите изменить:"
    keyboard = Keyboa(items=settings, items_in_row=1)
    bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard())


@bot.callback_query_handler(func=lambda call: call.data in settings)
def change_setting(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    dbutils.update_info(call.message.chat.id, call.data, empty_value)
    add_parameters(call.message)


def add_parameters(message):
    watermark_id, position, scale, opacity, padding, angle = dbutils.get_fields_info(message.chat.id,
                                                                                     "watermark_id, position, scale,"
                                                                                     "opacity, padding, angle")
    if watermark_id == empty_value:
        request_watermark_photo(message)
    elif position == empty_value:
        request_watermark_position(message)
    elif scale == empty_value:
        request_scale(message)
    elif opacity == empty_value:
        request_opacity(message)
    elif position != position_values[-1] and padding == empty_value:
        request_padding(message)
    elif angle == empty_value:
        request_angle(message)
    else:
        text = "Все параметры указаны. Отправьте фото, которое хочешь защитить"
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard())


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.chat.id
    if not check_settings(message):
        pass
    else:
        try:
            watermark_bytearray = download_photo(dbutils.get_fields_info(user_id, "watermark_id"))
            photo_path = download_photo(get_photo_id(message))
            photo_bytearray = process_photo(photo_path, watermark_bytearray, user_id)
            bot.send_photo(user_id, photo_bytearray)
        except Exception as e:
            bot.reply_to(message, str(e))


@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    print(message.document.file_name.split('.')[-1])
    if message.document.file_name.split('.')[-1] in photo_extensions:
        handle_photo(message)
    else:
        bot.send_message(chat_id=message.chat.id, text="Недопустимый тип файла")


def get_photo_id(message):
    photo_id = empty_value
    if message.photo is not None:
        photo_id = message.photo[len(message.photo) - 1].file_id
    elif message.document is not None:
        if message.document.file_name.split('.')[-1] in photo_extensions:
            photo_id = message.document.file_id
    return photo_id


def download_photo(file_id):
    file_info = bot.get_file(file_id=file_id)
    file_bytearray = bot.download_file(file_info.file_path)
    return file_bytearray


def send_to_all(text):
    for user_id in dbutils.get_all_users():
        try:
            bot.send_message(chat_id=user_id, text=text, reply_markup=get_reply_keyboard())
        except Exception as e:
            print(f'Не удалось отправить сообщение пользователю {user_id}\n' + str(e))


bot.polling(none_stop=True)
