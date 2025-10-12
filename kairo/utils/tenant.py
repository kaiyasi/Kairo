import sqlite3
import os
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import base64
import secrets
import json

@dataclass
class AttendanceSettings:
    rename_enabled: bool = False
    staff_role_id: Optional[int] = None
    rename_format_member: str = '{name}'
    rename_format_staff: str = '幹部 | {name}'

@dataclass
class BookkeepingSettings:
    start_row: int = 2
    date_col: str = 'A'
    category_col: str = 'B'
    amount_col: str = 'C'
    memo_col: str = 'D'
    user_col: str = 'E'

class TenantDB:
    def __init__(self, db_path: str = "kairo/data/tenant.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS orgs (
                    guild_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    admin_role_id INTEGER,
                    officer_role_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS org_configs (
                    guild_id INTEGER PRIMARY KEY,
                    ctfd_base_url TEXT,
                    ciphertext_ctfd_token TEXT,
                    ctfd_push_mode TEXT DEFAULT 'award',
                    ctfd_award_name TEXT DEFAULT 'Discord QA',
                    ctfd_award_category TEXT DEFAULT 'discord',
                    excel_path TEXT,
                    aes_key_b64 TEXT,
                    default_signin_ttl INTEGER DEFAULT 30,
                    canva_visible_after_signin BOOLEAN DEFAULT 1,
                    attendance_rename_enabled BOOLEAN DEFAULT 0,
                    attendance_staff_role_id INTEGER,
                    attendance_rename_format_member TEXT DEFAULT '{name}',
                    attendance_rename_format_staff TEXT DEFAULT '幹部 | {name}',
                    bookkeeping_layout TEXT,
                    google_sheets_url TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS org_modules (
                    guild_id INTEGER,
                    module TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    PRIMARY KEY (guild_id, module)
                );

                CREATE TABLE IF NOT EXISTS registration_status (
                    guild_id INTEGER PRIMARY KEY,
                    status TEXT DEFAULT 'none',
                    school TEXT,
                    club_name TEXT,
                    responsible_person TEXT,
                    responsible_discord_id INTEGER,
                    club_type TEXT,
                    reason TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS routing (
                    guild_id INTEGER,
                    key TEXT,
                    channel_id INTEGER,
                    PRIMARY KEY (guild_id, key)
                );

                CREATE TABLE IF NOT EXISTS plans (
                    guild_id INTEGER,
                    week_key TEXT,
                    group_name TEXT,
                    content TEXT NOT NULL,
                    PRIMARY KEY (guild_id, week_key, group_name)
                );

                CREATE TABLE IF NOT EXISTS plan_groups (
                    guild_id INTEGER,
                    user_id INTEGER,
                    group_name TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    expire_at TIMESTAMP NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    canva_url TEXT,
                    outline TEXT
                );

                CREATE TABLE IF NOT EXISTS records (
                    session_id INTEGER,
                    user_id INTEGER,
                    username TEXT NOT NULL,
                    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS scores (
                    guild_id INTEGER,
                    user_id INTEGER,
                    score INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                );

                CREATE TABLE IF NOT EXISTS ctfd_links (
                    guild_id INTEGER,
                    discord_user_id INTEGER,
                    email TEXT NOT NULL,
                    ctfd_user_id INTEGER,
                    PRIMARY KEY (guild_id, discord_user_id)
                );
            """)

    def register_org(self, guild_id: int, name: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("INSERT OR REPLACE INTO orgs (guild_id, name) VALUES (?, ?)", (guild_id, name))
                return True
            except sqlite3.Error:
                return False

    def get_org(self, guild_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM orgs WHERE guild_id = ?", (guild_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def is_module_enabled(self, guild_id: int, module: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT enabled FROM org_modules WHERE guild_id = ? AND module = ?", (guild_id, module))
            row = cursor.fetchone()
            return bool(row[0]) if row else True  # Default to enabled

    def set_module_enabled(self, guild_id: int, module: str, enabled: bool):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO org_modules (guild_id, module, enabled)
                VALUES (?, ?, ?)
            """, (guild_id, module, enabled))

    def enable_module(self, guild_id: int, module: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO org_modules (guild_id, module, enabled)
                VALUES (?, ?, 1)
            """, (guild_id, module))

    def get_attendance_settings(self, guild_id: int) -> AttendanceSettings:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM org_configs WHERE guild_id = ?", (guild_id,))
            row = cursor.fetchone()
            if row:
                return AttendanceSettings(
                    rename_enabled=bool(row['attendance_rename_enabled']),
                    staff_role_id=row['attendance_staff_role_id'],
                    rename_format_member=row['attendance_rename_format_member'],
                    rename_format_staff=row['attendance_rename_format_staff']
                )
        return AttendanceSettings()

    def set_attendance_setting(self, guild_id: int, key: str, value: Any):
        valid_keys = [
            'attendance_rename_enabled',
            'attendance_staff_role_id', 
            'attendance_rename_format_member',
            'attendance_rename_format_staff'
        ]
        if key not in valid_keys:
            raise ValueError(f"Invalid setting key: {key}")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO org_configs (guild_id) VALUES (?)", (guild_id,))
            conn.execute(f"UPDATE org_configs SET {key} = ? WHERE guild_id = ?", (value, guild_id))

    def get_bookkeeping_settings(self, guild_id: int) -> BookkeepingSettings:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT bookkeeping_layout FROM org_configs WHERE guild_id = ?", (guild_id,))
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    settings_dict = json.loads(row[0])
                    return BookkeepingSettings(**settings_dict)
                except (json.JSONDecodeError, TypeError):
                    return BookkeepingSettings()
        return BookkeepingSettings()

    def set_bookkeeping_settings(self, guild_id: int, settings: BookkeepingSettings):
        settings_json = json.dumps(asdict(settings))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR IGNORE INTO org_configs (guild_id) VALUES (?)", (guild_id,))
            conn.execute("UPDATE org_configs SET bookkeeping_layout = ? WHERE guild_id = ?", (settings_json, guild_id))

class CryptoManager:
    def __init__(self, master_key_b64: str):
        self.master_key = base64.b64decode(master_key_b64)
        if len(self.master_key) != 32:
            raise ValueError("Master key must be 32 bytes")

    def encrypt(self, plaintext: str) -> str:
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()

        encrypted_data = iv + encryptor.tag + ciphertext
        return base64.b64encode(encrypted_data).decode()

    def decrypt(self, ciphertext_b64: str) -> str:
        try:
            encrypted_data = base64.b64decode(ciphertext_b64)
            iv = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]

            cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(iv, tag))
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")

# Global instance
tenant_db = TenantDB()
