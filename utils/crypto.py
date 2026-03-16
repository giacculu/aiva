"""
Gestione crittografia per dati sensibili (diario segreto, chiavi)
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from loguru import logger
from typing import Optional, Union
from pathlib import Path

class CryptoManager:
    """
    Gestisce cifratura/decifratura dei dati sensibili.
    Usa Fernet (AES-128 in CBC mode con HMAC) per sicurezza.
    """
    
    def __init__(self, key: Optional[Union[str, bytes]] = None, salt: Optional[bytes] = None):
        """
        Inizializza il gestore con una chiave.
        
        Args:
            key: Chiave (stringa o bytes). Se None, ne genera una casuale.
            salt: Sale per derivazione chiave. Se None, usa un sale fisso (non sicuro per produzione).
        """
        if key is None:
            # Genera chiave casuale (per uso temporaneo)
            self.key = Fernet.generate_key()
            logger.warning("⚠️ Chiave crittografica generata casualmente. I dati non saranno recuperabili dopo il riavvio.")
        else:
            # Deriva chiave da password usando PBKDF2
            if isinstance(key, str):
                key = key.encode()
            
            if salt is None:
                # Sale fisso (solo per test! in produzione usare sale casuale e conservarlo)
                salt = b'AIVA_ai_fixed_salt_32_bytes_long!!'
            elif isinstance(salt, str):
                salt = salt.encode()
            
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(key))
            self.key = derived_key
        
        self.fernet = Fernet(self.key)
    
    def encrypt(self, data: Union[str, bytes]) -> bytes:
        """Cifra dati (stringa o bytes) e restituisce bytes cifrati."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.fernet.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decifra dati e restituisce bytes."""
        return self.fernet.decrypt(encrypted_data)
    
    def encrypt_to_base64(self, data: Union[str, bytes]) -> str:
        """Cifra e restituisce stringa base64 (utile per JSON)."""
        encrypted = self.encrypt(data)
        return base64.b64encode(encrypted).decode('ascii')
    
    def decrypt_from_base64(self, b64_data: str) -> bytes:
        """Decifra da stringa base64."""
        encrypted = base64.b64decode(b64_data)
        return self.decrypt(encrypted)
    
    def encrypt_file(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Cifra un file."""
        if output_path is None:
            output_path = input_path.with_suffix(input_path.suffix + '.enc')
        
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted = self.encrypt(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
        
        logger.debug(f"🔐 File cifrato: {input_path} -> {output_path}")
        return output_path
    
    def decrypt_file(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """Decifra un file."""
        if output_path is None:
            if input_path.suffix == '.enc':
                output_path = input_path.with_suffix('')
            else:
                output_path = input_path.with_suffix(input_path.suffix + '.dec')
        
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        
        data = self.decrypt(encrypted)
        
        with open(output_path, 'wb') as f:
            f.write(data)
        
        logger.debug(f"🔓 File decifrato: {input_path} -> {output_path}")
        return output_path


# Funzione di utilità per generare una chiave sicura
def generate_secure_key() -> str:
    """Genera una chiave sicura (da conservare in .env)."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode('ascii')


# Istanza globale (verrà configurata in run.py)
crypto = None