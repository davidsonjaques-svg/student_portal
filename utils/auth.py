import hashlib
from utils.database import get_db


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def login_user(email: str, password: str):
    conn = get_db()
    c = conn.cursor()
    pw_hash = hash_password(password)
    c.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?", (email, pw_hash))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def register_user(full_name, email, student_number, room_number, password):
    conn = get_db()
    c = conn.cursor()
    try:
        pw_hash = hash_password(password)
        c.execute("""
            INSERT INTO users (full_name, email, student_number, room_number, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (full_name, email, student_number, room_number, pw_hash))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        conn.close()
        if "UNIQUE" in str(e):
            if "email" in str(e):
                return {"success": False, "message": "This email is already registered."}
            return {"success": False, "message": "This student number is already registered."}
        return {"success": False, "message": str(e)}


def get_current_user(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None
