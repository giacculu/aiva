"""
AIVA 2.0 – FUNZIONI DI UTILITÀ
Funzioni generiche riutilizzabili in tutto il progetto.
"""

import re
import json
import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import emoji

def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    Carica JSON in modo sicuro.
    """
    try:
        return json.loads(text)
    except:
        return default if default is not None else {}

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronca testo a lunghezza massima.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_emojis(text: str) -> List[str]:
    """
    Estrae tutte le emoji da un testo.
    """
    return [c for c in text if emoji.is_emoji(c)]

def count_emojis(text: str) -> int:
    """
    Conta le emoji in un testo.
    """
    return emoji.emoji_count(text)

def random_string(length: int = 10, 
                  chars: str = string.ascii_letters + string.digits) -> str:
    """
    Genera stringa casuale.
    """
    return ''.join(random.choice(chars) for _ in range(length))

def generate_id(prefix: str = "") -> str:
    """
    Genera ID univoco.
    """
    import secrets
    random_part = secrets.token_hex(8)
    time_part = datetime.now().strftime("%Y%m%d%H%M%S")
    
    if prefix:
        return f"{prefix}_{time_part}_{random_part}"
    return f"{time_part}_{random_part}"

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """
    Hash di una stringa.
    """
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    else:
        return hashlib.sha256(text.encode()).hexdigest()

def format_timestamp(timestamp: Optional[datetime] = None, 
                    format: str = "%d/%m/%Y %H:%M") -> str:
    """
    Formatta timestamp.
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime(format)

def time_ago(timestamp: datetime, reference: Optional[datetime] = None) -> str:
    """
    Restituisce stringa tipo "2 ore fa".
    """
    if reference is None:
        reference = datetime.now()
    
    diff = reference - timestamp
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} anno{' fa' if years == 1 else ' fa'}"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} mese{' fa' if months == 1 else ' fa'}"
    elif diff.days > 0:
        return f"{diff.days} giorno{' fa' if diff.days == 1 else ' fa'}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} ora{' fa' if hours == 1 else ' fa'}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minuto{' fa' if minutes == 1 else ' fa'}"
    else:
        return "pochi secondi fa"

def extract_name(text: str) -> Optional[str]:
    """
    Estrae nome da testo come "mi chiamo X" o "sono X".
    """
    patterns = [
        r'mi chiamo\s+([A-Za-z]+)',
        r'sono\s+([A-Za-z]+)',
        r'(?:il|il mio) nome (?:è|e)\s+([A-Za-z]+)',
        r'chiamami\s+([A-Za-z]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).capitalize()
            # Filtra parole comuni
            if name.lower() not in ['qui', 'li', 'la', 'un', 'uno', 'una']:
                return name
    
    return None

def extract_age(text: str) -> Optional[int]:
    """
    Estrae età da testo.
    """
    patterns = [
        r'ho\s+(\d+)\s*anni',
        r'(\d+)\s*anni'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                age = int(match.group(1))
                if 13 < age < 100:  # range plausibile
                    return age
            except:
                pass
    
    return None

def extract_city(text: str) -> Optional[str]:
    """
    Estrae città da testo.
    """
    patterns = [
        r'vivo a\s+([A-Za-z\s]+)',
        r'abito a\s+([A-Za-z\s]+)',
        r'sono di\s+([A-Za-z\s]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            city = match.group(1).strip().capitalize()
            return city
    
    return None

def is_question(text: str) -> bool:
    """
    Verifica se un testo è una domanda.
    """
    return bool(re.search(r'\?$', text)) or bool(re.search(r'^(come|perché|dove|quando|chi|cosa|che)', text.lower()))

def is_greeting(text: str) -> bool:
    """
    Verifica se un testo è un saluto.
    """
    greetings = ['ciao', 'salve', 'hey', 'buongiorno', 'buonasera', 'buon pomeriggio']
    return any(g in text.lower() for g in greetings)

def is_farewell(text: str) -> bool:
    """
    Verifica se un testo è un commiato.
    """
    farewells = ['ciao', 'arrivederci', 'a dopo', 'a presto', 'notte', 'buonanotte']
    return any(f in text.lower() for f in farewells)

def clean_text(text: str) -> str:
    """
    Pulisce testo da caratteri speciali.
    """
    # Rimuovi caratteri di controllo
    text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
    # Normalizza spazi
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text(text: str, max_length: int = 4000) -> List[str]:
    """
    Divide testo in chunk per limiti Telegram.
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        
        # Cerca ultimo punto prima del limite
        split_at = text[:max_length].rfind('.')
        if split_at == -1:
            split_at = text[:max_length].rfind(' ')
        
        if split_at == -1:
            split_at = max_length
        
        chunks.append(text[:split_at + 1])
        text = text[split_at + 1:].lstrip()
    
    return chunks

def normalize_text(text: str) -> str:
    """
    Normalizza testo (lowercase, rimuovi punteggiatura).
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    Divisione sicura.
    """
    try:
        return a / b if b != 0 else default
    except:
        return default

# Istanza globale (opzionale)
helpers = {
    "safe_json_loads": safe_json_loads,
    "truncate_text": truncate_text,
    "extract_emojis": extract_emojis,
    "count_emojis": count_emojis,
    "random_string": random_string,
    "generate_id": generate_id,
    "hash_string": hash_string,
    "format_timestamp": format_timestamp,
    "time_ago": time_ago,
    "extract_name": extract_name,
    "extract_age": extract_age,
    "extract_city": extract_city,
    "is_question": is_question,
    "is_greeting": is_greeting,
    "is_farewell": is_farewell,
    "clean_text": clean_text,
    "chunk_text": chunk_text,
    "normalize_text": normalize_text,
    "safe_divide": safe_divide
}