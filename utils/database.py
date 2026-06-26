import sqlite3
import os

DB_PATH = "reslife.db"


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            student_number TEXT UNIQUE NOT NULL,
            room_number TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            profile_bio TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            admin_response TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            pinned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            urgent INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Seed admin account
    import hashlib
    admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("""
        INSERT OR IGNORE INTO users (full_name, email, student_number, room_number, password_hash, role)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("Admin Manager", "admin@reslife.co.za", "ADMIN001", "Office", admin_hash, "admin"))

    # Seed sample data
    c.execute("SELECT COUNT(*) FROM notices")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO notices (user_id, title, body, category, pinned)
            VALUES (1, 'Welcome to ResLife Portal!', 
            'This portal is your central hub for everything at the residence. Log queries, read notices, and stay connected with management. We hope you have a great year!', 
            'general', 1)
        """)
        c.execute("""
            INSERT INTO announcements (user_id, title, body, urgent)
            VALUES (1, 'Water Shutdown Notice', 
            'Scheduled maintenance on Thursday 3 July from 08:00–12:00. Please store water in advance. Apologies for the inconvenience.', 1)
        """)
        c.execute("""
            INSERT INTO announcements (user_id, title, body, urgent)
            VALUES (1, 'Laundry Room Hours Updated', 
            'The laundry room is now open from 06:00 to 22:00 daily. Please respect quiet hours and clean up after use.', 0)
        """)

    conn.commit()
    conn.close()
