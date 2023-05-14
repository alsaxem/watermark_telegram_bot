import sqlite3

db_name = "bot.db"

conn = sqlite3.connect(database=db_name, check_same_thread=False)
c = conn.cursor()


def create_users_table():
    c.execute("CREATE TABLE IF NOT EXISTS users ("
              "user_id INTEGER PRIMARY KEY NOT NULL,"
              "name TEXT NOT NULL,"
              "watermark_id TEXT,"
              "position TEXT,"
              "scale FLOAT,"
              "opacity FLOAT,"
              "angle INTEGER, "
              "padding FLOAT,"
              "language TEXT)")


def drop_table(table_name="users"):
    c.execute("DROP TABLE " + table_name)


def get_fields_info(user_id, fields):
    c.execute("SELECT " + fields + " FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if data:
        data = list(data)
    return data


def get_all_info(user_id):
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()


def get_all_users():
    c.execute("SELECT user_id FROM users")
    return [item[0] for item in c.fetchall()]


def add_user(*args):
    c.execute("INSERT OR REPLACE INTO users (user_id, name, watermark_id, position, scale, opacity, "
              "padding, angle, language)"
              "VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL)", args)
    conn.commit()


def update_info(user_id, column, value):
    if type(value) is str:
        value = "\"" + value + "\""
    if value is None:
        value = "NULL"
    c.execute("UPDATE users SET " + column + "=" + str(value) + " WHERE user_id = " + str(user_id))
    conn.commit()


def is_user_exist(user_id):
    return bool(get_fields_info(user_id, "user_id"))


create_users_table()
