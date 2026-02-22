import sqlite3
import os
import logging

DB_PATH = os.environ.get("DB_PATH", "seen_articles.db")

def init_db():
    \"\"\"Initialize the SQLite database.\"\"\"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seen_urls (
                url TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    except Exception as e:
        logging.error(f"Error initializing DB: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def is_url_seen(url):
    \"\"\"Check if a URL has already been processed.\"\"\"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM seen_urls WHERE url = ?", (url,))
        result = cursor.fetchone()
        return bool(result)
    except Exception as e:
        logging.error(f"Error checking URL: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def mark_url_seen(url):
    \"\"\"Mark a URL as processed.\"\"\"
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO seen_urls (url) VALUES (?)", (url,))
        conn.commit()
    except Exception as e:
        logging.error(f"Error marking URL as seen: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
