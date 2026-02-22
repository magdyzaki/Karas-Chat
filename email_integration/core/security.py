"""
نظام الأمان والخصوصية
Security and Privacy System
"""
import os
import base64
import json
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SECURITY_DIR = os.path.join(BASE_DIR, "database", "security")
SECURITY_KEY_FILE = os.path.join(SECURITY_DIR, "key.key")
SECURITY_CONFIG_FILE = os.path.join(SECURITY_DIR, "security_config.json")

os.makedirs(SECURITY_DIR, exist_ok=True)


def get_or_create_key(password: Optional[str] = None) -> bytes:
    """
    الحصول على مفتاح التشفير أو إنشاء مفتاح جديد
    
    Args:
        password: كلمة المرور (اختياري) - إذا تم توفيرها، سيتم استخدامها لتوليد المفتاح
    
    Returns:
        مفتاح التشفير
    """
    if password:
        # استخدام كلمة المرور لتوليد مفتاح
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'efm_salt_2024',  # في الإنتاج، يجب أن يكون salt عشوائي لكل مستخدم
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    # إذا كان هناك مفتاح موجود، استخدمه
    if os.path.exists(SECURITY_KEY_FILE):
        with open(SECURITY_KEY_FILE, 'rb') as f:
            return f.read()
    
    # إنشاء مفتاح جديد
    key = Fernet.generate_key()
    with open(SECURITY_KEY_FILE, 'wb') as f:
        f.write(key)
    return key


def encrypt_data(data: str, password: Optional[str] = None) -> str:
    """
    تشفير البيانات
    
    Args:
        data: البيانات المراد تشفيرها
        password: كلمة المرور (اختياري)
    
    Returns:
        البيانات المشفرة (base64)
    """
    try:
        key = get_or_create_key(password)
        f = Fernet(key)
        encrypted = f.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    except Exception as e:
        print(f"Error encrypting data: {e}")
        return data  # إرجاع البيانات الأصلية في حالة الخطأ


def decrypt_data(encrypted_data: str, password: Optional[str] = None) -> str:
    """
    فك تشفير البيانات
    
    Args:
        encrypted_data: البيانات المشفرة
        password: كلمة المرور (اختياري)
    
    Returns:
        البيانات الأصلية
    """
    try:
        key = get_or_create_key(password)
        f = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_data.encode())
        decrypted = f.decrypt(encrypted_bytes)
        return decrypted.decode()
    except Exception as e:
        print(f"Error decrypting data: {e}")
        return encrypted_data  # إرجاع البيانات المشفرة في حالة الخطأ


def is_security_enabled() -> bool:
    """التحقق من تفعيل الأمان"""
    if not os.path.exists(SECURITY_CONFIG_FILE):
        return False
    
    try:
        with open(SECURITY_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('enabled', False)
    except:
        return False


def set_security_enabled(enabled: bool):
    """تفعيل أو تعطيل الأمان"""
    config = {'enabled': enabled}
    with open(SECURITY_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def hash_password(password: str) -> str:
    """
    تشفير كلمة المرور (hash)
    
    Args:
        password: كلمة المرور
    
    Returns:
        كلمة المرور المشفرة
    """
    from hashlib import sha256
    return sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """
    التحقق من كلمة المرور
    
    Args:
        password: كلمة المرور الأصلية
        hashed: كلمة المرور المشفرة
    
    Returns:
        True إذا كانت صحيحة، False خلاف ذلك
    """
    return hash_password(password) == hashed
