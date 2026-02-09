"""
نظام إدارة المستندات
Documents Management System
"""
import os
import shutil
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")


def ensure_documents_directory():
    """إنشاء مجلد المستندات إذا لم يكن موجوداً"""
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    return DOCUMENTS_DIR


def get_client_documents_directory(client_id: int):
    """الحصول على مسار مجلد مستندات العميل"""
    ensure_documents_directory()
    client_dir = os.path.join(DOCUMENTS_DIR, f"client_{client_id}")
    os.makedirs(client_dir, exist_ok=True)
    return client_dir


def save_document_file(source_path: str, client_id: int, file_name: str) -> str:
    """
    حفظ ملف مستند في مجلد العميل
    
    Returns:
        مسار الملف المحفوظ
    """
    client_dir = get_client_documents_directory(client_id)
    
    # تنظيف اسم الملف (إزالة الأحرف غير المسموحة)
    safe_filename = "".join(c for c in file_name if c.isalnum() or c in "._- ")
    safe_filename = safe_filename.strip()
    
    # إذا كان الملف موجوداً، إضافة timestamp
    dest_path = os.path.join(client_dir, safe_filename)
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(safe_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{name}_{timestamp}{ext}"
        dest_path = os.path.join(client_dir, safe_filename)
    
    # نسخ الملف
    shutil.copy2(source_path, dest_path)
    
    return dest_path


def get_file_size(file_path: str) -> int:
    """الحصول على حجم الملف بالبايت"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def get_file_type(file_name: str) -> str:
    """تحديد نوع الملف من الامتداد"""
    ext = os.path.splitext(file_name)[1].lower()
    
    type_mapping = {
        '.pdf': 'PDF',
        '.doc': 'Word',
        '.docx': 'Word',
        '.xls': 'Excel',
        '.xlsx': 'Excel',
        '.txt': 'Text',
        '.jpg': 'Image',
        '.jpeg': 'Image',
        '.png': 'Image',
        '.zip': 'Archive',
        '.rar': 'Archive'
    }
    
    return type_mapping.get(ext, 'Unknown')


def format_file_size(size_bytes: int) -> str:
    """تنسيق حجم الملف"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
