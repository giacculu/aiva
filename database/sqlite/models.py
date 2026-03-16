"""
Modelli SQLite per AIVA AI
Memoria fattuale e conversazioni strutturate
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from loguru import logger

class SQLiteDatabase:
    """
    Gestisce il database SQLite per memoria semantica e conversazioni.
    Thread-safe con context manager.
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Crea le tabelle se non esistono."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabella conversazioni
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    mood TEXT,
                    sentiment_score REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Tabella fatti utente (memoria semantica)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    confidence REAL DEFAULT 1.0,
                    source_message_id INTEGER,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, key)
                )
            ''')
            
            # Tabella pagamenti
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    payment_id TEXT UNIQUE NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'EUR',
                    status TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    metadata TEXT
                )
            ''')
            
            # Tabella interazioni significative (per memoria episodica)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS significant_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    emotional_impact TEXT,
                    importance REAL DEFAULT 0.5,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    conversation_ids TEXT  -- JSON array di ID conversazioni correlate
                )
            ''')
            
            # Indici per performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_time ON conversations(user_id, timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_facts_user ON user_facts(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id, status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_significant_user ON significant_interactions(user_id)')
            
            conn.commit()
            logger.debug(f"✅ Database SQLite inizializzato: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager per connessioni thread-safe."""
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ========== CONVERSAZIONI ==========
    
    def add_message(self, user_id: str, role: str, content: str, 
                   mood: Optional[str] = None, 
                   sentiment_score: Optional[float] = None,
                   metadata: Optional[Dict] = None) -> int:
        """Aggiunge un messaggio alla cronologia."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (user_id, role, content, mood, sentiment_score, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, role, content, mood, sentiment_score, 
                  json.dumps(metadata) if metadata else None))
            conn.commit()
            return cursor.lastrowid
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Recupera la cronologia recente di un utente."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, mood, sentiment_score, timestamp
                FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()
            
            # Restituisce in ordine cronologico
            history = []
            for row in reversed(rows):
                history.append({
                    'role': row['role'],
                    'content': row['content'],
                    'mood': row['mood'],
                    'sentiment': row['sentiment_score'],
                    'timestamp': row['timestamp']
                })
            return history
    
    def get_recent_messages(self, user_id: str, minutes: int = 60) -> List[Dict]:
        """Recupera messaggi degli ultimi N minuti."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, timestamp
                FROM conversations
                WHERE user_id = ? AND datetime(timestamp) > datetime('now', ?)
                ORDER BY timestamp
            ''', (user_id, f'-{minutes} minutes'))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== FATTI UTENTE ==========
    
    def remember_fact(self, user_id: str, key: str, value: str, 
                     category: str = 'general', 
                     confidence: float = 1.0,
                     source_message_id: Optional[int] = None) -> None:
        """Salva o aggiorna un fatto sull'utente."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_facts (user_id, key, value, category, confidence, source_message_id, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value = excluded.value,
                    confidence = excluded.confidence,
                    source_message_id = excluded.source_message_id,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, key.lower(), value, category, confidence, source_message_id))
            conn.commit()
    
    def recall_fact(self, user_id: str, key: str) -> Optional[str]:
        """Recupera un fatto specifico."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT value FROM user_facts
                WHERE user_id = ? AND key = ?
            ''', (user_id, key.lower()))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def recall_all_facts(self, user_id: str) -> Dict[str, str]:
        """Recupera tutti i fatti di un utente."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT key, value FROM user_facts
                WHERE user_id = ?
            ''', (user_id,))
            return {row['key']: row['value'] for row in cursor.fetchall()}
    
    def forget_fact(self, user_id: str, key: str) -> None:
        """Rimuove un fatto."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM user_facts
                WHERE user_id = ? AND key = ?
            ''', (user_id, key.lower()))
            conn.commit()
    
    # ========== PAGAMENTI ==========
    
    def add_payment(self, user_id: str, payment_id: str, amount: float,
                   status: str = 'created', metadata: Optional[Dict] = None) -> None:
        """Registra un pagamento."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (user_id, payment_id, amount, status, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, payment_id, amount, status, json.dumps(metadata) if metadata else None))
            conn.commit()
    
    def update_payment_status(self, payment_id: str, status: str) -> None:
        """Aggiorna stato pagamento."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status == 'completed':
                cursor.execute('''
                    UPDATE payments
                    SET status = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE payment_id = ?
                ''', (status, payment_id))
            else:
                cursor.execute('''
                    UPDATE payments
                    SET status = ?
                    WHERE payment_id = ?
                ''', (status, payment_id))
            conn.commit()
    
    def get_user_payments(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        """Recupera pagamenti di un utente."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute('''
                    SELECT * FROM payments
                    WHERE user_id = ? AND status = ?
                    ORDER BY created_at DESC
                ''', (user_id, status))
            else:
                cursor.execute('''
                    SELECT * FROM payments
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_spent(self, user_id: str, days: Optional[int] = None) -> float:
        """Calcola totale speso da un utente (opzionalmente negli ultimi giorni)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if days:
                cursor.execute('''
                    SELECT SUM(amount) as total FROM payments
                    WHERE user_id = ? AND status = 'completed'
                    AND datetime(completed_at) > datetime('now', ?)
                ''', (user_id, f'-{days} days'))
            else:
                cursor.execute('''
                    SELECT SUM(amount) as total FROM payments
                    WHERE user_id = ? AND status = 'completed'
                ''', (user_id,))
            row = cursor.fetchone()
            return row['total'] or 0.0
    
    # ========== INTERAZIONI SIGNIFICATIVE ==========
    
    def add_significant_interaction(self, user_id: str, summary: str,
                                   emotional_impact: Optional[str] = None,
                                   importance: float = 0.5,
                                   conversation_ids: Optional[List[int]] = None) -> int:
        """Registra un'interazione significativa per memoria episodica."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO significant_interactions (user_id, summary, emotional_impact, importance, conversation_ids)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, summary, emotional_impact, importance, 
                  json.dumps(conversation_ids) if conversation_ids else None))
            conn.commit()
            return cursor.lastrowid
    
    def get_significant_interactions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Recupera le interazioni più importanti con un utente."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM significant_interactions
                WHERE user_id = ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]