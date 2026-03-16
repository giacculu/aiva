"""
AIVA 2.0 – MODELLI DATABASE
Schema SQLite per la memoria persistente.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from loguru import logger

class Database:
    """
    Gestisce la connessione al database SQLite.
    """
    
    # Schema del database (suddiviso in singole istruzioni)
    CREATE_TABLES = [
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            mood TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_user 
        ON conversations(user_id)
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_time 
        ON conversations(timestamp)
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            confidence REAL DEFAULT 1.0,
            source TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            times_mentioned INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT 1,
            metadata TEXT,
            UNIQUE(user_id, key)
        )
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_facts_user 
        ON user_facts(user_id)
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_facts_key 
        ON user_facts(key)
        """,
        
        """
        CREATE TABLE IF NOT EXISTS fact_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact_id INTEGER,
            old_value TEXT,
            new_value TEXT,
            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY(fact_id) REFERENCES user_facts(id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS user_metadata (
            user_id TEXT PRIMARY KEY,
            first_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_messages INTEGER DEFAULT 0,
            trust_level REAL DEFAULT 0.5,
            intimacy_level REAL DEFAULT 0.0,
            notes TEXT,
            metadata TEXT
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'EUR',
            payment_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'completed',
            metadata TEXT
        )
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_payments_user 
        ON payments(user_id)
        """,
        
        """
        CREATE TRIGGER IF NOT EXISTS update_user_last_interaction
        AFTER INSERT ON conversations
        BEGIN
            INSERT OR REPLACE INTO user_metadata (user_id, last_interaction, total_messages)
            VALUES (
                NEW.user_id,
                CURRENT_TIMESTAMP,
                COALESCE((SELECT total_messages + 1 FROM user_metadata WHERE user_id = NEW.user_id), 1)
            );
        END
        """
    ]
    
    def __init__(self, db_path: str = "data/AIVA.db"):
        """
        Inizializza il database.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        
        logger.info(f"💾 Database inizializzato: {db_path}")
    
    def _init_db(self):
        """Crea le tabelle se non esistono"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            # Esegui ogni istruzione separatamente
            for statement in self.CREATE_TABLES:
                try:
                    cursor.execute(statement)
                except sqlite3.OperationalError as e:
                    logger.error(f"❌ Errore SQL: {e}\nStatement: {statement[:100]}...")
                    raise
            conn.commit()
    
    @contextmanager
    def get_conn(self):
        """Fornisce una connessione thread-safe"""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ===== CONVERSAZIONI =====
    
    def save_message(self, user_id: str, role: str, content: str, 
                     mood: Optional[str] = None, metadata: Optional[Dict] = None):
        """Salva un messaggio"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (user_id, role, content, mood, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, role, content, mood, 
                  json.dumps(metadata) if metadata else None))
            conn.commit()
    
    def get_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Recupera cronologia conversazioni"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, mood, timestamp FROM conversations
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]  # ordine cronologico
    
    # ===== FATTI =====
    
    def remember_fact(self, user_id: str, key: str, value: Any,
                     category: str = 'general', confidence: float = 1.0,
                     source: str = 'conversation'):
        """Salva un fatto su un utente"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            
            # Controlla se esiste già
            cursor.execute("""
                SELECT id, value FROM user_facts
                WHERE user_id = ? AND key = ? AND is_active = 1
            """, (user_id, key))
            
            existing = cursor.fetchone()
            
            if existing:
                fact_id = existing[0]
                old_value = existing[1]
                
                if str(old_value) != str(value):
                    cursor.execute("""
                        UPDATE user_facts
                        SET value = ?, last_updated = CURRENT_TIMESTAMP,
                            confidence = ?, times_mentioned = times_mentioned + 1
                        WHERE id = ?
                    """, (str(value), confidence, fact_id))
                    
                    cursor.execute("""
                        INSERT INTO fact_history (fact_id, old_value, new_value, reason)
                        VALUES (?, ?, ?, ?)
                    """, (fact_id, old_value, str(value), source))
            else:
                cursor.execute("""
                    INSERT INTO user_facts (user_id, key, value, category, confidence, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, key, str(value), category, confidence, source))
            
            conn.commit()
    
    def recall_fact(self, user_id: str, key: str) -> Optional[str]:
        """Recupera un fatto specifico"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM user_facts
                WHERE user_id = ? AND key = ? AND is_active = 1
            """, (user_id, key))
            
            row = cursor.fetchone()
            return row[0] if row else None
    
    def recall_all_facts(self, user_id: str) -> Dict:
        """Recupera tutti i fatti su un utente"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT key, value, category FROM user_facts
                WHERE user_id = ? AND is_active = 1
            """, (user_id,))
            
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    # ===== PAGAMENTI =====
    
    def save_payment(self, user_id: str, amount: float, payment_id: Optional[str] = None,
                    metadata: Optional[Dict] = None):
        """Registra un pagamento"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO payments (user_id, amount, payment_id, metadata)
                VALUES (?, ?, ?, ?)
            """, (user_id, amount, payment_id, 
                  json.dumps(metadata) if metadata else None))
            conn.commit()
    
    def get_user_payments(self, user_id: str) -> List[Dict]:
        """Recupera pagamenti di un utente"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT amount, timestamp, status FROM payments
                WHERE user_id = ?
                ORDER BY timestamp DESC
            """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_total_paid(self, user_id: str) -> float:
        """Totale pagato da un utente"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(amount) FROM payments
                WHERE user_id = ? AND status = 'completed'
            """, (user_id,))
            
            row = cursor.fetchone()
            return row[0] if row[0] else 0.0
    
    # ===== UTENTI =====
    
    def get_user_metadata(self, user_id: str) -> Dict:
        """Recupera metadata di un utente"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_metadata WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    def update_user_note(self, user_id: str, note: str):
        """Aggiunge una nota su un utente"""
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_metadata (user_id, notes)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    notes = notes || '\n' || ?
            """, (user_id, note, note))
            conn.commit()

# Istanza globale
db = Database()