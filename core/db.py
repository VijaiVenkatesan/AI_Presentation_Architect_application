import sqlite3

# IMPORTANT: Use /tmp for Streamlit Cloud
DB_PATH = "/tmp/app.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Create users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # Create projects table
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
