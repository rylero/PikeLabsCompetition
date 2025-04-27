import sqlite3
from typing import List, Optional
import json, os

class ChatMessageHistoryDB:
    def __init__(self, filepath=os.path.abspath("../data/messages.db")) -> None:
        self.db_conn = sqlite3.connect(filepath)

        self.initialize_db()
    
    def is_database_initialized(self) -> bool:
        cursor = self.db_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='ChatHistory'
        """)
        
        result =  self.cursor.fetchone()
        
        return result is not None
    
    def initialize_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ChatHistory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                url TEXT,
                messages TEXT
            )
        ''')

        self.db_conn.commit()

    def get_message_history(self, email: str, url: str) -> Optional[dict]:
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT id, email, url, messages FROM ChatHistory WHERE email=? AND url=?
        ''', (email,url,))
        
        result = self.cursor.fetchone()
        
        if result:
            article = json.loads(result[1])
            return article
        
        return None
    
    def create_messsage_history(
        self, email, url, messages
    ) -> int:
        cursor = self.db_conn.cursor()
        id = cursor.execute('''
            INSERT INTO ChatHistory (
                email,
                url,
                messages
            ) VALUES (?,?,?)
        ''', (
            email,
            url,
            json.dumps(messages) if messages else "[]",
        ))

        id = cursor.lastrowid
        
        self.db_conn.commit()

        return id
    
    def update_message_history(
        self, email, url, messages
    ) -> bool:
        cursor = self.db_conn.cursor()
        id = cursor.execute('''
            UPDATE ChatHistory
            SET messages = ?
            WHERE email=? AND url=?;
        ''', (
            json.dumps(messages) if messages else "[]",
            email, url,
        ))
        
        self.db_conn.commit()

        return id

    def close(self):
        self.db_conn.close()