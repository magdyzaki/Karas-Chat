"""
نظام النسخ الاحتياطي التلقائي
Backup and Restore System for EFM
"""
import os
import shutil
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

from .db import DB_PATH, BASE_DIR

# مسار مجلد النسخ الاحتياطية
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
CONFIG_FILE = os.path.join(BASE_DIR, "database", "backup_config.json")


def ensure_backup_dir():
    """إنشاء مجلد النسخ الاحتياطية إن لم يكن موجوداً"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)


def get_backup_config() -> Dict:
    """قراءة إعدادات النسخ الاحتياطي"""
    ensure_backup_dir()
    
    default_config = {
        "auto_backup_enabled": False,
        "backup_frequency": "daily",  # daily, weekly
        "backup_time": "02:00",  # وقت النسخ اليومي
        "keep_backups": 30,  # عدد النسخ المحفوظة
        "backup_on_startup": True,
        "last_backup": None
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved_config = json.load(f)
                default_config.update(saved_config)
        except Exception:
            pass
    
    return default_config


def save_backup_config(config: Dict):
    """حفظ إعدادات النسخ الاحتياطي"""
    ensure_backup_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def create_backup(description: str = "") -> Optional[str]:
    """
    إنشاء نسخة احتياطية من قاعدة البيانات
    
    Returns:
        مسار الملف الاحتياطي أو None في حالة الفشل
    """
    try:
        ensure_backup_dir()
        
        if not os.path.exists(DB_PATH):
            return None
        
        # اسم الملف: efm_backup_YYYY-MM-DD_HH-MM-SS.db
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"efm_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # نسخ قاعدة البيانات
        shutil.copy2(DB_PATH, backup_path)
        
        # إنشاء ملف معلومات عن النسخة
        info_filename = f"efm_backup_{timestamp}.info"
        info_path = os.path.join(BACKUP_DIR, info_filename)
        
        db_size = os.path.getsize(DB_PATH)
        info = {
            "backup_file": backup_filename,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "db_size": db_size,
            "version": "1.0"
        }
        
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        # تحديث الإعدادات
        config = get_backup_config()
        config["last_backup"] = datetime.now().isoformat()
        save_backup_config(config)
        
        # تنظيف النسخ القديمة
        cleanup_old_backups()
        
        return backup_path
        
    except Exception as e:
        print(f"خطأ في النسخ الاحتياطي: {e}")
        return None


def cleanup_old_backups():
    """حذف النسخ الاحتياطية القديمة بناءً على الإعدادات"""
    try:
        config = get_backup_config()
        keep_count = config.get("keep_backups", 30)
        
        if not os.path.exists(BACKUP_DIR):
            return
        
        # الحصول على جميع ملفات النسخ الاحتياطي
        backup_files = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith("efm_backup_") and filename.endswith(".db"):
                file_path = os.path.join(BACKUP_DIR, filename)
                backup_files.append({
                    "path": file_path,
                    "name": filename,
                    "created": os.path.getctime(file_path)
                })
        
        # ترتيب حسب التاريخ (الأحدث أولاً)
        backup_files.sort(key=lambda x: x["created"], reverse=True)
        
        # حذف النسخ الزائدة
        if len(backup_files) > keep_count:
            for backup in backup_files[keep_count:]:
                try:
                    os.remove(backup["path"])
                    # حذف ملف المعلومات المرتبط
                    info_path = backup["path"].replace(".db", ".info")
                    if os.path.exists(info_path):
                        os.remove(info_path)
                except Exception:
                    pass
                    
    except Exception as e:
        print(f"خطأ في تنظيف النسخ القديمة: {e}")


def list_backups() -> List[Dict]:
    """الحصول على قائمة بجميع النسخ الاحتياطية"""
    backups = []
    
    if not os.path.exists(BACKUP_DIR):
        return backups
    
    try:
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith("efm_backup_") and filename.endswith(".db"):
                file_path = os.path.join(BACKUP_DIR, filename)
                info_path = file_path.replace(".db", ".info")
                
                backup_info = {
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "created": datetime.fromtimestamp(os.path.getctime(file_path)),
                    "description": ""
                }
                
                # قراءة معلومات إضافية من ملف info
                if os.path.exists(info_path):
                    try:
                        with open(info_path, "r", encoding="utf-8") as f:
                            info = json.load(f)
                            backup_info["description"] = info.get("description", "")
                            backup_info["created"] = datetime.fromisoformat(info.get("created_at", backup_info["created"].isoformat()))
                    except Exception:
                        pass
                
                backups.append(backup_info)
        
        # ترتيب حسب التاريخ (الأحدث أولاً)
        backups.sort(key=lambda x: x["created"], reverse=True)
        
    except Exception as e:
        print(f"خطأ في قراءة قائمة النسخ: {e}")
    
    return backups


def restore_backup(backup_path: str) -> bool:
    """
    استعادة قاعدة البيانات من نسخة احتياطية
    
    Args:
        backup_path: مسار ملف النسخة الاحتياطية
        
    Returns:
        True في حالة النجاح، False في حالة الفشل
    """
    try:
        if not os.path.exists(backup_path):
            return False
        
        # التحقق من صحة ملف النسخة الاحتياطية
        try:
            conn = sqlite3.connect(backup_path)
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            conn.close()
        except Exception:
            return False
        
        # إنشاء نسخة احتياطية من الملف الحالي قبل الاستعادة
        current_backup = create_backup("قبل الاستعادة من نسخة قديمة")
        
        # إغلاق أي اتصالات مفتوحة بقاعدة البيانات
        # (في حالة الاستخدام الحقيقي، قد نحتاج لإغلاق التطبيق أولاً)
        
        # استعادة النسخة
        shutil.copy2(backup_path, DB_PATH)
        
        return True
        
    except Exception as e:
        print(f"خطأ في الاستعادة: {e}")
        return False


def should_run_auto_backup() -> bool:
    """التحقق من الحاجة لتشغيل النسخ الاحتياطي التلقائي"""
    try:
        config = get_backup_config()
        
        if not config.get("auto_backup_enabled", False):
            return False
        
        last_backup_str = config.get("last_backup")
        if not last_backup_str:
            return True
        
        try:
            last_backup = datetime.fromisoformat(last_backup_str)
            now = datetime.now()
            
            frequency = config.get("backup_frequency", "daily")
            
            if frequency == "daily":
                # نسخ يومي: إذا مر أكثر من 24 ساعة
                return (now - last_backup).total_seconds() >= 86400
            elif frequency == "weekly":
                # نسخ أسبوعي: إذا مر أكثر من 7 أيام
                return (now - last_backup).days >= 7
        except (ValueError, TypeError):
            # إذا كان تنسيق التاريخ غير صحيح، قم بالنسخ
            return True
        
        return False
        
    except Exception:
        return False


def run_auto_backup_if_needed():
    """تشغيل النسخ الاحتياطي التلقائي إن لزم الأمر"""
    if should_run_auto_backup():
        return create_backup("نسخ احتياطي تلقائي")
    return None


def get_backup_statistics() -> Dict:
    """الحصول على إحصائيات النسخ الاحتياطية"""
    backups = list_backups()
    config = get_backup_config()
    
    total_size = sum(b["size"] for b in backups)
    
    return {
        "total_backups": len(backups),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "last_backup": config.get("last_backup"),
        "auto_backup_enabled": config.get("auto_backup_enabled", False),
        "keep_backups": config.get("keep_backups", 30)
    }
