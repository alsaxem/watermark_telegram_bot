import sqlite3
from config import db_name

conn = sqlite3.connect(db_name)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS texts
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT UNIQUE)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS languages
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT UNIQUE)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS text_languages
                  (text_id INTEGER,
                   lang_id INTEGER,
                   content TEXT,
                   FOREIGN KEY (text_id) REFERENCES texts (id),
                   FOREIGN KEY (lang_id) REFERENCES languages (id),
                   PRIMARY KEY (text_id, lang_id))''')


languages = ['en', 'ua', 'ru']
texts = [
    {'title': 'hello', 'content': {'en': 'Welcome.\nBot will help you protect your image with a watermark.', 'ua': 'Ласкаво просимо.\nБот допоможе вам захистити зображення водяним знаком.', 'ru': 'Добро пожаловать.\nБот поможет вам защитить изображение водяным знаком.'}},

]


for text in texts:
    cursor.execute('SELECT id FROM texts WHERE title = ?', (text['title'],))
    result = cursor.fetchone()

    if result:
        text_id = result[0]
    else:
        cursor.execute('INSERT OR REPLACE INTO texts (title) VALUES (?)', (text['title'],))
        text_id = cursor.lastrowid

    for lang in languages:
        cursor.execute('SELECT id FROM languages WHERE name = ?', (lang,))
        result = cursor.fetchone()

        if result:
            lang_id = result[0]
        else:
            cursor.execute('INSERT OR REPLACE INTO languages (name) VALUES (?)', (lang,))
            lang_id = cursor.lastrowid

        content = text['content'][lang]
        cursor.execute('INSERT OR REPLACE INTO text_languages (text_id, lang_id, content) VALUES (?, ?, ?)', (text_id, lang_id, content))


conn.commit()
conn.close()
