import sqlite3
from config import db_name, dictionary_name, languages


def create_tables(cursor):
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


def parse_data(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    data = []
    current_entry = {}

    for line in lines:
        line = line.strip()

        if line.startswith('title:'):
            current_entry['title'] = line.split(':', 1)[1].strip()
        elif line.startswith('content:'):
            current_entry['content'] = {}
        elif line:
            lang, text = line.split(':', 1)
            current_entry['content'][lang.strip()] = text.strip()
        else:
            data.append(current_entry)
            current_entry = {}

    return data


def insert_text(cursor, texts):
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
            cursor.execute('INSERT OR REPLACE INTO text_languages (text_id, lang_id, content) VALUES (?, ?, ?)',
                           (text_id, lang_id, content))


def start():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    create_tables(cursor)
    texts = parse_data(dictionary_name)
    insert_text(cursor, texts)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    start()
