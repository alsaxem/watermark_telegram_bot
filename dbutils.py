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
              "padding FLOAT, "
              "angle INTEGER"
              "language TEXT)")


def drop_table(table_name="users"):
    c.execute("DROP TABLE " + table_name)


def get_fields_info(user_id, fields):
    c.execute("SELECT " + fields + " FROM users WHERE user_id=?", (user_id,))
    if "," in fields:
        fields_info = c.fetchone()
    else:
        fields_info, = c.fetchone()
    return fields_info


def get_all_info(user_id):
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()


def add_user(*args):
    c.execute("INSERT OR REPLACE INTO users (user_id, name, watermark_id, position, scale, opacity, "
              "padding, angle ,language)"
              "VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL)", args)
    conn.commit()


def update_info(user_id, column, value):
    if type(value) is str:
        value = "\"" + value + "\""
    c.execute("UPDATE users SET " + column + "=" + value + " WHERE user_id = " + str(user_id))
    conn.commit()


def is_user_exist(user_id):
    return bool(get_fields_info(user_id, "user_id"))
