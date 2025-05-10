import sqlite3
from typing import List, Optional
import json, os
import datetime

class AnalysisCache:
    def __init__(self, filepath=os.path.abspath("../data/analysiscache.db")) -> None:
        self.db_conn = sqlite3.connect(filepath, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.cursor = self.db_conn.cursor()

        self.initialize_db()

    def is_database_initialized(self) -> bool:
        self.cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='Articles'
        """)
        
        result = self.cursor.fetchone()
        
        return result is not None
    
    def initialize_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                factuality REAL,
                factuality_description TEXT,
                bias REAL,
                bias_description TEXT,
                opposing_links TEXT,
                agreement_links TEXT,
                show_bias BOOLEAN,
                expire_date TIMESTAMP
            )
        ''')

        self.db_conn.commit()

    def find_article_by_url(self, url: str) -> Optional[dict]:
        self.cursor.execute('''
            SELECT id, url, factuality, factuality_description, 
                bias, bias_description, opposing_links, agreement_links, show_bias, expire_date
            FROM Articles 
            WHERE url = ?
        ''', (url,))
        
        result = self.cursor.fetchone()
        
        if not result:
            return None
        expired = datetime.datetime.now() > result[-1]
        if expired:
            # TODO: Delete article that is expired from database, prevent large cache file
            return None
        
        # Convert tuple to dictionary and parse JSON strings
        article = {
            'id': result[0],
            'url': result[1],
            'factuality': result[2],
            'factuality_description': result[3],
            'bias': result[4],
            'bias_description': result[5],
            'opposing_links': json.loads(result[6]) if result[6] else [],
            'agreement_links': json.loads(result[7]) if result[7] else [],
            'show_bias': bool(result[8]),
        }
        return article
    
    def generate_expire_date(self):
        return datetime.datetime.now() + datetime.timedelta(days=2)

    def add_article(
        self,
        url: str,
        factuality: Optional[float] = None,
        factuality_description: Optional[str] = None,
        bias: Optional[float] = None,
        bias_description: Optional[str] = None,
        opposing_links: Optional[List[str]] = None,
        agreement_links: Optional[List[str]] = None,
        show_bias: Optional[bool] = True
    ) -> bool:
        try:
            self.cursor.execute('''
                INSERT INTO Articles (
                    url, factuality, factuality_description, bias,
                    bias_description, opposing_links, agreement_links, show_bias, expire_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url,
                factuality,
                factuality_description,
                bias,
                bias_description,
                json.dumps(opposing_links) if opposing_links else None,
                json.dumps(agreement_links) if agreement_links else None,
                show_bias,
                self.generate_expire_date()
            ))
            
            self.db_conn.commit()
            success = True

        except sqlite3.IntegrityError:
            # URL already exists
            success = False
        
        return success

    def close(self):
        self.db_conn.close()