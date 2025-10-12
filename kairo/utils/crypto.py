import base64
import hashlib
import urllib.parse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import secrets
import io
import discord

def base64_encode(text: str) -> str:
    """Base64 encode"""
    return base64.b64encode(text.encode()).decode()

def base64_decode(text: str) -> str:
    """Base64 decode"""
    try:
        return base64.b64decode(text).decode()
    except Exception as e:
        raise ValueError(f"Base64 解碼失敗: {str(e)}")

def url_encode(text: str) -> str:
    """URL encode"""
    return urllib.parse.quote(text)

def url_decode(text: str) -> str:
    """URL decode"""
    try:
        return urllib.parse.unquote(text)
    except Exception as e:
        raise ValueError(f"URL 解碼失敗: {str(e)}")

def hex_encode(text: str) -> str:
    """Hex encode"""
    return text.encode().hex()

def hex_decode(text: str) -> str:
    """Hex decode"""
    try:
        return bytes.fromhex(text).decode()
    except Exception as e:
        raise ValueError(f"Hex 解碼失敗: {str(e)}")

def md5_hash(text: str) -> str:
    """MD5 hash"""
    return hashlib.md5(text.encode()).hexdigest()

def sha1_hash(text: str) -> str:
    """SHA1 hash"""
    return hashlib.sha1(text.encode()).hexdigest()

def sha256_hash(text: str) -> str:
    """SHA256 hash"""
    return hashlib.sha256(text.encode()).hexdigest()

def caesar_encrypt(text: str, shift: int = 3) -> str:
    """Caesar cipher encryption"""
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
        else:
            result += char
    return result

def caesar_decrypt(text: str, shift: int = 3) -> str:
    """Caesar cipher decryption"""
    return caesar_encrypt(text, -shift)

def vigenere_encrypt(text: str, key: str) -> str:
    """Vigenère cipher encryption"""
    if not key:
        raise ValueError("Vigenère 加密需要密鑰")

    key = key.upper()
    result = ""
    key_index = 0

    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            key_char = key[key_index % len(key)]
            shift = ord(key_char) - 65
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            key_index += 1
        else:
            result += char
    return result

def vigenere_decrypt(text: str, key: str) -> str:
    """Vigenère cipher decryption"""
    if not key:
        raise ValueError("Vigenère 解密需要密鑰")

    key = key.upper()
    result = ""
    key_index = 0

    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            key_char = key[key_index % len(key)]
            shift = ord(key_char) - 65
            result += chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
            key_index += 1
        else:
            result += char
    return result

def atbash_cipher(text: str) -> str:
    """Atbash cipher (symmetric)"""
    result = ""
    for char in text:
        if char.isalpha():
            if char.isupper():
                result += chr(90 - (ord(char) - 65))
            else:
                result += chr(122 - (ord(char) - 97))
        else:
            result += char
    return result

def rot13_cipher(text: str) -> str:
    """ROT13 cipher (symmetric)"""
    return caesar_encrypt(text, 13)

def railfence_encrypt(text: str, rails: int = 3) -> str:
    """Rail fence cipher encryption"""
    if rails <= 1:
        return text

    fence = [['' for _ in range(len(text))] for _ in range(rails)]
    rail = 0
    direction = 1

    for i, char in enumerate(text):
        fence[rail][i] = char
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction *= -1

    result = ""
    for row in fence:
        result += ''.join(row)

    return result

def railfence_decrypt(text: str, rails: int = 3) -> str:
    """Rail fence cipher decryption"""
    if rails <= 1:
        return text

    # Create pattern
    fence = [['' for _ in range(len(text))] for _ in range(rails)]
    rail = 0
    direction = 1

    for i in range(len(text)):
        fence[rail][i] = '*'
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction *= -1

    # Fill fence with text
    index = 0
    for i in range(rails):
        for j in range(len(text)):
            if fence[i][j] == '*' and index < len(text):
                fence[i][j] = text[index]
                index += 1

    # Read result
    result = ""
    rail = 0
    direction = 1

    for i in range(len(text)):
        result += fence[rail][i]
        rail += direction
        if rail == rails - 1 or rail == 0:
            direction *= -1

    return result

MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.', ' ': '/'
}

MORSE_DECODE = {v: k for k, v in MORSE_CODE.items()}

def morse_encrypt(text: str) -> str:
    """Morse code encryption"""
    result = []
    for char in text.upper():
        if char in MORSE_CODE:
            result.append(MORSE_CODE[char])
        else:
            result.append(char)
    return ' '.join(result)

def morse_decrypt(text: str) -> str:
    """Morse code decryption"""
    words = text.split(' / ')
    result = []

    for word in words:
        letters = word.split(' ')
        word_result = ""
        for letter in letters:
            if letter in MORSE_DECODE:
                word_result += MORSE_DECODE[letter]
            elif letter:
                word_result += letter
        result.append(word_result)

    return ' '.join(result)

def aes_gcm_encrypt(text: str, key_b64: str) -> str:
    """AES-GCM encryption"""
    try:
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("密鑰必須為 32 字節")

        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(text.encode()) + encryptor.finalize()

        encrypted_data = iv + encryptor.tag + ciphertext
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        raise ValueError(f"AES-GCM 加密失敗: {str(e)}")

def aes_gcm_decrypt(ciphertext_b64: str, key_b64: str) -> str:
    """AES-GCM decryption"""
    try:
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("密鑰必須為 32 字節")

        encrypted_data = base64.b64decode(ciphertext_b64)
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]

        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()
    except Exception as e:
        raise ValueError(f"AES-GCM 解密失敗: {str(e)}")

def aes_cbc_encrypt(text: str, key_b64: str) -> str:
    """AES-CBC encryption"""
    try:
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("密鑰必須為 32 字節")

        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        # Add PKCS7 padding
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(text.encode()) + padder.finalize()

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        raise ValueError(f"AES-CBC 加密失敗: {str(e)}")

def aes_cbc_decrypt(ciphertext_b64: str, key_b64: str) -> str:
    """AES-CBC decryption"""
    try:
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("密鑰必須為 32 字節")

        encrypted_data = base64.b64decode(ciphertext_b64)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove PKCS7 padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode()
    except Exception as e:
        raise ValueError(f"AES-CBC 解密失敗: {str(e)}")

# Crypto function mapping
CRYPTO_FUNCTIONS = {
    'base64': (base64_encode, base64_decode),
    'urlencode': (url_encode, url_decode),
    'urldecode': (url_decode, url_encode),
    'hex': (hex_encode, hex_decode),
    'hexdecode': (hex_decode, hex_encode),
    'md5': (md5_hash, None),
    'sha1': (sha1_hash, None),
    'sha256': (sha256_hash, None),
    'caesar': (caesar_encrypt, caesar_decrypt),
    'vigenere': (vigenere_encrypt, vigenere_decrypt),
    'atbash': (atbash_cipher, atbash_cipher),
    'rot13': (rot13_cipher, rot13_cipher),
    'railfence': (railfence_encrypt, railfence_decrypt),
    'morse': (morse_encrypt, morse_decrypt),
    'aes-gcm': (aes_gcm_encrypt, aes_gcm_decrypt),
    'aesgcm': (aes_gcm_encrypt, aes_gcm_decrypt),
    'aes-cbc': (aes_cbc_encrypt, aes_cbc_decrypt),
    'aescbc': (aes_cbc_encrypt, aes_cbc_decrypt),
}

def is_long_text(text: str) -> bool:
    """Check if text is too long for Discord embed"""
    return len(text) > 1500

async def create_text_file(content: str, filename: str) -> discord.File:
    """Create Discord file from text content"""
    file_buffer = io.StringIO(content)
    return discord.File(file_buffer, filename=filename)