from wmbed.telegram_api import *
import telebot
from keyboa import Keyboa
from config import *
from bot_token import *
import dbutils
import text_DB_inserter

bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start(message):
    dbutils.add_user(message.chat.id, message.from_user.first_name + " " + message.from_user.last_name)
    request_language(message)


def send_start_message(message):
    text = dbutils.get_text("hello", message.chat.id)
    text = text.replace("\\n", "\n")
    bot.send_message(chat_id=message.chat.id, text=text)
    add_parameters(message)


@bot.message_handler(commands=['sendall'])
def sendall(message):
    if message.chat.id == owner_id:
        send_to_all(message.text.replace("/sendall", ""))


def request_language(message):
    text = dbutils.get_text("request_language", message.chat.id)
    languages_localize = []
    for language in languages:
        languages_localize.append(dbutils.get_text("language_"+language, message.chat.id))
    keyboard = Keyboa(items=languages_localize)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_watermark_photo(message):
    text = dbutils.get_text("request_photo", message.chat.id)
    bot.send_message(chat_id=message.chat.id, text=text)
    bot.register_next_step_handler(message, set_watermark_photo)


def request_watermark_position(message):
    text = dbutils.get_text("request_position", message.chat.id)
    value = dbutils.get_text("position_FILLING", message.chat.id)
    position_prints_local = position_prints[:-1] + [value]
    keyboard = Keyboa(items=position_prints_local, items_in_row=3)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_scale(message):
    text = dbutils.get_text("request_scale", message.chat.id)
    keyboard = Keyboa(items=scale_values, items_in_row=5)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_opacity(message):
    text = dbutils.get_text("request_opacity", message.chat.id)
    keyboard = Keyboa(items=opacity_values, items_in_row=5)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_padding(message):
    text = dbutils.get_text("request_padding", message.chat.id)
    keyboard = Keyboa(items=padding_values, items_in_row=5)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


def request_angle(message):
    text = dbutils.get_text("request_angle", message.chat.id)
    bot.send_message(chat_id=message.chat.id, text=text)
    bot.register_next_step_handler(message, set_angle)


def request_noise(message):
    text = dbutils.get_text("request_noise", message.chat.id)
    text = text.replace("\\n", "\n")
    values = [dbutils.get_text("True", message.chat.id)]
    values += [dbutils.get_text("False", message.chat.id)]
    keyboard = Keyboa(items=values, items_in_row=2)
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=keyboard())


@bot.callback_query_handler(func=lambda call: dbutils.get_setting_name(call.data, "language_") in languages)
def set_language(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    dbutils.update_info(call.message.chat.id, "language", dbutils.get_setting_name(call.data, "language_"))
    send_start_message(call.message)


def set_watermark_photo(message):
    try:
        photo_id = get_photo_id(message)
        if photo_id != empty_value:
            dbutils.update_info(message.chat.id, "watermark_id", photo_id)
            text = dbutils.get_text("sign_added", message.chat.id)
            bot.send_message(chat_id=message.chat.id, text=text)
        else:
            text = dbutils.get_text("wt_photo_only", message.chat.id)
            bot.send_message(chat_id=message.chat.id, text=text)
        add_parameters(message)
    except Exception as e:
        print("ERROR: set_watermark_photo")
        print(e)
        process_exception(message)
        request_watermark_photo(message)


@bot.callback_query_handler(func=lambda call: dbutils.get_setting_name(call.data, "") in position_prints)
def set_position(call):
    try:
        value = dbutils.get_setting_name(call.data, "")
        value = position_values[position_prints.index(value)]
        set_parameter(call.message, column="position", data=value)
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
        request_angle(message)


@bot.callback_query_handler(func=lambda call: dbutils.get_setting_name(call.data, "") in noise_values)
def set_noise(call):
    try:
        value = dbutils.get_setting_name(call.data, "")
        set_parameter(call.message, column="noise", data=value)
    except Exception as e:
        print("ERROR: set_scale")
        print(e)
        process_exception(call.message)
        request_noise(call.message)


def set_parameter(message, column, data, is_remove=True):
    if is_remove:
        bot.delete_message(message.chat.id, message.message_id)
    dbutils.update_info(message.chat.id, column, data)
    add_parameters(message)


def process_exception(message):
    text = dbutils.get_text("something_wrong", message.chat.id)
    bot.send_message(chat_id=message.chat.id, text=text)


def get_reply_keyboard(user_id):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    text = dbutils.get_text("my_settings", user_id)
    button1 = telebot.types.KeyboardButton(text)
    text = dbutils.get_text("change_settings", user_id)
    button2 = telebot.types.KeyboardButton(text)
    keyboard.add(button1, button2)
    return keyboard


def process_photo(photo_bytearray, watermark_bytearray, user_id):
    position, scale, opacity, padding, angle, noise = dbutils.get_fields_info(user_id,
                                                                              "position, scale, opacity, padding, "
                                                                              "angle, noise")
    if noise == "True":
        noise = True
    else:
        noise = False
    if position == "FILLING":
        photo_bytearray = create_image_with_watermark_tiling(
            image_bytearray=photo_bytearray,
            watermark_bytearray=watermark_bytearray,
            scale=scale,
            angle=angle,
            opacity=opacity,
            add_noise=noise
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
            add_noise=noise
        )
    return photo_bytearray


@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == dbutils.get_text("my_settings", message.chat.id):
        send_settings(message.chat.id)
    elif message.text == dbutils.get_text("change_settings", message.chat.id):
        request_change_setting(message.chat.id)
    elif check_settings(message):
        text = dbutils.get_text("send_photo", message.chat.id)
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard(message.chat.id))


def check_settings(message):
    user_data = dbutils.get_fields_info(message.chat.id,
                                        "watermark_id, position, scale, opacity, angle, noise, padding")
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
    setting_names = settings[1:]
    setting_values = dbutils.get_fields_info(user_id, ", ".join(setting_names))
    if not setting_values:
        setting_values = [empty_value] * setting_names.len()
    for i in range(0, len(setting_names)):
        setting_name = dbutils.get_text("setting_"+setting_names[i], user_id)
        if setting_values[i] in position_values:
            setting_value = dbutils.get_text("position_" + setting_values[i], user_id)
        elif setting_values[i] in languages:
            setting_value = dbutils.get_text("language_" + setting_values[i], user_id)
        elif setting_values[i] in noise_values + [empty_value]:
            setting_value = dbutils.get_text(str(setting_values[i]), user_id)
        else:
            setting_value = setting_values[i]
        user_settings += f"{setting_name}: {setting_value}\n"
    bot.send_message(chat_id=user_id, text=user_settings)


def request_change_setting(user_id):
    text = dbutils.get_text("select_parameter", user_id)
    keyboard = Keyboa(items=get_setting_names(user_id), items_in_row=1)
    bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard())


@bot.callback_query_handler(func=lambda call: dbutils.get_setting_name(call.data) in settings)
def change_setting(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    data = dbutils.get_setting_name(call.data)
    if data == "language":
        request_language(call.message)
    else:
        dbutils.update_info(call.message.chat.id, dbutils.get_setting_name(call.data), empty_value)
        add_parameters(call.message)


def get_setting_names(user_id):
    items = []
    for item in settings:
        items.append(dbutils.get_text("setting_" + item, user_id))
    return items


def add_parameters(message):
    watermark_id, position, scale, opacity, padding, angle, noise = dbutils.get_fields_info(message.chat.id,
                                                                                            "watermark_id, position, "
                                                                                            "scale, opacity, padding, "
                                                                                            "angle, noise")
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
    elif noise == empty_value:
        request_noise(message)
    else:
        text = dbutils.get_text("parameters_specified", message.chat.id)
        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=get_reply_keyboard(message.chat.id))


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
        text = dbutils.get_text("invalid_file_type", message.chat.id)
        bot.send_message(chat_id=message.chat.id, text=text)


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
            bot.send_message(chat_id=user_id, text=text)
        except Exception as e:
            print(f'Failed to send a message to the user {user_id}\n' + str(e))


text_DB_inserter.start()
bot.polling(none_stop=True)
