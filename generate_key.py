#!/usr/bin/env python3
"""
生成 Kairo 機器人所需的 MASTER_KEY_BASE64
"""

import secrets
import base64

def generate_master_key():
    """生成 32 字節的隨機密鑰並轉換為 Base64"""
    # 生成 32 字節隨機密鑰
    key_bytes = secrets.token_bytes(32)

    # 轉換為 Base64
    key_b64 = base64.b64encode(key_bytes).decode()

    return key_b64

if __name__ == "__main__":
    print("🔑 Kairo 機器人密鑰生成器")
    print("=" * 40)

    key = generate_master_key()

    print(f"生成的 MASTER_KEY_BASE64:")
    print(f"{key}")
    print()
    print("請將此密鑰添加到您的 .env 檔案中：")
    print(f"MASTER_KEY_BASE64={key}")
    print()
    print("⚠️  重要提醒：")
    print("- 請妥善保管此密鑰")
    print("- 不要將密鑰上傳到版本控制系統")
    print("- 遺失此密鑰將無法解密已儲存的敏感資料")