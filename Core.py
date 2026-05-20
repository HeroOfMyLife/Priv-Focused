from cryptography.hazmat.primitives import hashes
import json
import hashlib
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class IdentityVault:
    def __init__(self, master_password):
        self.master_password = master_password
        self.backend = default_backend()
        self.salt = os.urandom(16)
        self.key = self._derive_key()

    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(self.master_password.encode('utf-8'))

    def encrypt_data(self, data_dict):
        """Encrypts a dictionary of identities into .AADI bytes"""
        json_data = json.dumps(data_dict).encode('utf-8')
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(json_data) + encryptor.finalize()
        
        # .AADI Format: MAGIC + IV + SALT + CIPHERTEXT + TAG
        return b'AADI_ID' + iv + self.salt + ciphertext + encryptor.tag

    def decrypt_data(self, aadi_bytes):
        """Decrypts .AADI bytes back to dictionary"""
        if not aadi_bytes.startswith(b'AADI_ID'):
            raise ValueError("Invalid .AADI file format")
            
        iv = aadi_bytes[7:19]
        salt = aadi_bytes[19:35]
        # The rest is ciphertext + tag (last 16 bytes are tag)
        ciphertext = aadi_bytes[35:-16]
        tag = aadi_bytes[-16:]
        
        # Re-derive key using the salt from the file
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=self.backend
        )
        key = kdf.derive(self.master_password.encode('utf-8'))
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=self.backend)
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return json.loads(plaintext.decode('utf-8'))

    # Helper to save/load to disk
    def save_vault(self, filepath, data_dict):
        encrypted = self.encrypt_data(data_dict)
        with open(filepath, 'wb') as f:
            f.write(encrypted)

    def load_vault(self, filepath):
        with open(filepath, 'rb') as f:
            return self.decrypt_data(f.read())