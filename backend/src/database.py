import sqlite3
import json
import os
import datetime
from typing import Dict, List, Optional, Tuple

class DatabaseManager:
    def __init__(self, db_path: str = "instagram_bot.db"):
        """Initialize database manager"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    session_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    proxy TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create dm_tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dm_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_username TEXT NOT NULL,
                    recipient_username TEXT NOT NULL,
                    message_text TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'sent',
                    thread_id TEXT,
                    message_id TEXT
                )
            ''')
            
            # Create daily_stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    date DATE NOT NULL,
                    dms_sent INTEGER DEFAULT 0,
                    dms_failed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username, date)
                )
            ''')
            
            # Create usernames table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usernames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    firstname TEXT,
                    is_processed BOOLEAN DEFAULT 0,
                    processed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def save_session(self, username: str, session_data: Dict) -> bool:
        """Save or update session for a username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                session_json = json.dumps(session_data)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions (username, session_data, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (username, session_json))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving session for {username}: {e}")
            return False
    
    def get_session(self, username: str) -> Optional[Dict]:
        """Get session data for a username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT session_data FROM sessions 
                    WHERE username = ? AND is_active = 1
                ''', (username,))
                
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return None
        except Exception as e:
            print(f"Error getting session for {username}: {e}")
            return None
    
    def delete_session(self, username: str) -> bool:
        """Delete session for a username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE sessions SET is_active = 0 
                    WHERE username = ?
                ''', (username,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting session for {username}: {e}")
            return False
    
    def save_account(self, username: str, password: str, proxy: str = None) -> bool:
        """Save or update account"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO accounts (username, password, proxy, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (username, password, proxy))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving account {username}: {e}")
            return False
    
    def get_accounts(self) -> List[Dict]:
        """Get all active accounts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT username, password, proxy FROM accounts 
                    WHERE is_active = 1
                ''')
                
                accounts = []
                for row in cursor.fetchall():
                    accounts.append({
                        'username': row[0],
                        'password': row[1],
                        'proxy': row[2]
                    })
                return accounts
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []
    
    def delete_account(self, username: str) -> bool:
        """Delete account"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE accounts SET is_active = 0 
                    WHERE username = ?
                ''', (username,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting account {username}: {e}")
            return False
    
    def track_dm_sent(self, sender_username: str, recipient_username: str, 
                     message_text: str = None, thread_id: str = None, 
                     message_id: str = None) -> bool:
        """Track a sent DM"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert DM tracking record
                cursor.execute('''
                    INSERT INTO dm_tracking 
                    (sender_username, recipient_username, message_text, thread_id, message_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sender_username, recipient_username, message_text, thread_id, message_id))
                
                # Update daily stats
                today = datetime.date.today().isoformat()
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats (username, date, dms_sent)
                    VALUES (?, ?, COALESCE(
                        (SELECT dms_sent FROM daily_stats WHERE username = ? AND date = ?), 0
                    ) + 1)
                ''', (sender_username, today, sender_username, today))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error tracking DM: {e}")
            return False
    
    def track_dm_failed(self, sender_username: str, recipient_username: str, 
                       error_message: str = None) -> bool:
        """Track a failed DM"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert DM tracking record with failed status
                cursor.execute('''
                    INSERT INTO dm_tracking 
                    (sender_username, recipient_username, message_text, status)
                    VALUES (?, ?, ?, 'failed')
                ''', (sender_username, recipient_username, error_message))
                
                # Update daily stats
                today = datetime.date.today().isoformat()
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_stats (username, date, dms_failed)
                    VALUES (?, ?, COALESCE(
                        (SELECT dms_failed FROM daily_stats WHERE username = ? AND date = ?), 0
                    ) + 1)
                ''', (sender_username, today, sender_username, today))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error tracking failed DM: {e}")
            return False
    
    def get_daily_stats(self, username: str, date: str = None) -> Dict:
        """Get daily statistics for a username"""
        if date is None:
            date = datetime.date.today().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT dms_sent, dms_failed FROM daily_stats 
                    WHERE username = ? AND date = ?
                ''', (username, date))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'username': username,
                        'date': date,
                        'dms_sent': result[0] or 0,
                        'dms_failed': result[1] or 0
                    }
                return {
                    'username': username,
                    'date': date,
                    'dms_sent': 0,
                    'dms_failed': 0
                }
        except Exception as e:
            print(f"Error getting daily stats: {e}")
            return {
                'username': username,
                'date': date,
                'dms_sent': 0,
                'dms_failed': 0
            }
    
    def get_total_dms_today(self, username: str) -> int:
        """Get total DMs sent today by a username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                today = datetime.date.today().isoformat()
                cursor.execute('''
                    SELECT dms_sent FROM daily_stats 
                    WHERE username = ? AND date = ?
                ''', (username, today))
                
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"Error getting total DMs today: {e}")
            return 0
    
    def save_usernames(self, usernames: List[str], firstnames: Dict[str, str] = None) -> bool:
        """Save usernames to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for username in usernames:
                    firstname = firstnames.get(username, "") if firstnames else ""
                    cursor.execute('''
                        INSERT OR IGNORE INTO usernames (username, firstname)
                        VALUES (?, ?)
                    ''', (username, firstname))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving usernames: {e}")
            return False
    
    def get_unprocessed_usernames(self, limit: int = None) -> List[str]:
        """Get unprocessed usernames"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if limit:
                    cursor.execute('''
                        SELECT username FROM usernames 
                        WHERE is_processed = 0 
                        ORDER BY created_at ASC 
                        LIMIT ?
                    ''', (limit,))
                else:
                    cursor.execute('''
                        SELECT username FROM usernames 
                        WHERE is_processed = 0 
                        ORDER BY created_at ASC
                    ''')
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting unprocessed usernames: {e}")
            return []
    
    def mark_username_processed(self, username: str) -> bool:
        """Mark username as processed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE usernames 
                    SET is_processed = 1, processed_at = CURRENT_TIMESTAMP 
                    WHERE username = ?
                ''', (username,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error marking username processed: {e}")
            return False
    
    def get_analytics(self) -> Dict:
        """Get overall analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total accounts
                cursor.execute('SELECT COUNT(*) FROM accounts WHERE is_active = 1')
                total_accounts = cursor.fetchone()[0]
                
                # Total DMs sent today
                today = datetime.date.today().isoformat()
                cursor.execute('''
                    SELECT SUM(dms_sent) FROM daily_stats WHERE date = ?
                ''', (today,))
                total_dms_today = cursor.fetchone()[0] or 0
                
                # Total DMs failed today
                cursor.execute('''
                    SELECT SUM(dms_failed) FROM daily_stats WHERE date = ?
                ''', (today,))
                total_failed_today = cursor.fetchone()[0] or 0
                
                # Unprocessed usernames
                cursor.execute('SELECT COUNT(*) FROM usernames WHERE is_processed = 0')
                unprocessed_usernames = cursor.fetchone()[0]
                
                # Active sessions
                cursor.execute('SELECT COUNT(*) FROM sessions WHERE is_active = 1')
                active_sessions = cursor.fetchone()[0]
                
                return {
                    'total_accounts': total_accounts,
                    'total_dms_today': total_dms_today,
                    'total_failed_today': total_failed_today,
                    'unprocessed_usernames': unprocessed_usernames,
                    'active_sessions': active_sessions
                }
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {
                'total_accounts': 0,
                'total_dms_today': 0,
                'total_failed_today': 0,
                'unprocessed_usernames': 0,
                'active_sessions': 0
            }

# Global database instance
db = DatabaseManager() 