import sqlite3

def init_db():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        content TEXT
    )""")

    conn.commit()
    conn.close()


def save_project(user_id, content):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("INSERT INTO projects (user_id, content) VALUES (?, ?)", (user_id, content))
    conn.commit()
    conn.close()
