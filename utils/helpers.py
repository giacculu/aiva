"""
Funzioni di utilità generiche
"""
import re
import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import json
from pathlib import Path

def random_string(length: int = 10) -> str:
    """Genera una stringa casuale alfanumerica."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def random_emoji(emojis: Optional[List[str]] = None) -> str:
    """Sceglie un emoji casuale da una lista predefinita."""
    if emojis is None:
        emojis = ["😊", "🥰", "✨", "💕", "❤️", "😌", "🤔", "😴", "🥱", "🎉"]
    return random.choice(emojis)

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Tronca un testo se supera la lunghezza massima."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def safe_json_loads(text: str, default: Any = None) -> Any:
    """Carica JSON in modo sicuro, restituendo default in caso di errore."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default

def extract_mentions(text: str) -> List[str]:
    """Estrae menzioni (@username) da un testo."""
    return re.findall(r'@(\w+)', text)

def extract_hashtags(text: str) -> List[str]:
    """Estrae hashtag da un testo."""
    return re.findall(r'#(\w+)', text)

def time_ago(timestamp: datetime) -> str:
    """Restituisce una stringa tipo '5 minuti fa'."""
    now = datetime.now()
    delta = now - timestamp
    
    if delta < timedelta(minutes=1):
        return "pochi secondi fa"
    elif delta < timedelta(hours=1):
        minutes = delta.seconds // 60
        return f"{minutes} minuti fa"
    elif delta < timedelta(days=1):
        hours = delta.seconds // 3600
        return f"{hours} ore fa"
    elif delta < timedelta(days=30):
        days = delta.days
        return f"{days} giorni fa"
    else:
        return timestamp.strftime("%d/%m/%Y")

def format_datetime(dt: datetime, format: str = "%d/%m/%Y %H:%M") -> str:
    """Formatta data e ora."""
    return dt.strftime(format)

def slugify(text: str) -> str:
    """Converte un testo in slug (es. "Ciao Mondo!" -> "ciao-mondo")."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def ensure_directory(path: Path) -> Path:
    """Assicura che una directory esista, creandola se necessario."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def parse_bool(value: Union[str, bool, int, None]) -> bool:
    """Converte vari valori in booleano."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'on', 'y')
    return False

def merge_dicts(dict1: Dict, dict2: Dict, deep: bool = True) -> Dict:
    """Unisce due dizionari (deep merge se richiesto)."""
    if not deep:
        return {**dict1, **dict2}
    
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value
    return result

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Divide una lista in chunks di dimensione massima chunk_size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def get_file_extension(filename: str) -> str:
    """Restituisce l'estensione di un file (senza punto)."""
    return Path(filename).suffix.lower().lstrip('.')

def is_image_file(filename: str) -> bool:
    """Verifica se un file è un'immagine in base all'estensione."""
    ext = get_file_extension(filename)
    return ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp')

def is_video_file(filename: str) -> bool:
    """Verifica se un file è un video in base all'estensione."""
    ext = get_file_extension(filename)
    return ext in ('mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm')