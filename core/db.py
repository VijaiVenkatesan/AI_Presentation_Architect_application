import sqlite3
import hashlib

DB_PATH = "/tmp/app.db"  # MUST match db.py


def get_connection():
    return sqlite3.connect(DB_PATH)


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def signup(username, password):
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        conn.close()
        return True, "Signup successful"

    except Exception as e:
        conn.close()
        return False, str(e)


def login(username, password):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )

    user = c.fetchone()
    conn.close()

    if user:
        return True, user
    else:
        return False, "Invalid username or password"
