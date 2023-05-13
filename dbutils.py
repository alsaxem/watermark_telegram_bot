import sqlite3

db_name = "bot.db"

conn = sqlite3.connect(database=db_name)
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
    c.execute("INSERT OR IGNORE INTO users (user_id, name)"
              "VALUES (?, ?)", args)
    conn.commit()


def update_info(user_id, field, value):
    c.execute("UPDATE users SET " + field + " = " + value + " WHERE user_id = " + user_id)
    conn.commit()

