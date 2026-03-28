import sqlite3

DB_PATH = "/tmp/app.db"  # Streamlit Cloud safe


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_project(user_id, content):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "INSERT INTO projects (user_id, content) VALUES (?, ?)",
        (user_id, content)
    )

    conn.commit()
    conn.close()
