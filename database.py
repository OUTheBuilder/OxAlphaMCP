import sqlite3, os, time

DB_PATH = os.path.join(os.path.dirname(__file__), "oxalpha.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        invite_code TEXT,
        api_key TEXT DEFAULT '',
        provider TEXT DEFAULT 'openrouter',
        model TEXT DEFAULT 'openai/gpt-4o-mini',
        created_at REAL
    );
    CREATE TABLE IF NOT EXISTS pills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        icon TEXT DEFAULT '💊',
        prompt TEXT NOT NULL,
        created_at REAL
    );
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        agent TEXT DEFAULT '',
        created_at REAL
    );
    """)
    db.commit()
    db.close()

def hash_password(pw: str) -> str:
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()

INVITE_CODES = {"OXALPHA2024", "BULLRUN"}
