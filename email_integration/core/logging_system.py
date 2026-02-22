"""
نظام Logging شامل للبرنامج
Comprehensive Logging System for EFM
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# مسار ملفات الـ Log
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# مسارات الملفات
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
APP_LOG_FILE = LOGS_DIR / "app.log"
SYNC_LOG_FILE = LOGS_DIR / "sync.log"

# إعدادات الـ Logging
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # عدد ملفات النسخ الاحتياطي


class EFMLogger:
    """مدير Logging للبرنامج"""
    
    def __init__(self):
        self.setup_loggers()
    
    def setup_loggers(self):
        """إعداد Loggers المختلفة"""
        # 1. Logger للأخطاء
        self.error_logger = logging.getLogger("EFM_Error")
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.handlers.clear()
        
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
        
        # 2. Logger للتطبيق العام
        self.app_logger = logging.getLogger("EFM_App")
        self.app_logger.setLevel(logging.INFO)
        self.app_logger.handlers.clear()
        
        app_handler = RotatingFileHandler(
            APP_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        app_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        app_handler.setFormatter(app_formatter)
        self.app_logger.addHandler(app_handler)
        
        # 3. Logger للمزامنة
        self.sync_logger = logging.getLogger("EFM_Sync")
        self.sync_logger.setLevel(logging.INFO)
        self.sync_logger.handlers.clear()
        
        sync_handler = RotatingFileHandler(
            SYNC_LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        sync_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        sync_handler.setFormatter(sync_formatter)
        self.sync_logger.addHandler(sync_handler)
    
    def log_error(self, error: Exception, context: str = "", additional_info: dict = None):
        """تسجيل خطأ"""
        try:
            message = f"[{context}] {str(error)}"
            if additional_info:
                info_str = ", ".join([f"{k}={v}" for k, v in additional_info.items()])
                message += f" | {info_str}"
            
            self.error_logger.error(message, exc_info=True)
            
            # أيضاً في ملف التطبيق العام
            self.app_logger.error(message)
        except Exception:
            pass  # لا نريد أن يفشل Logging نفسه
    
    def log_warning(self, message: str, context: str = ""):
        """تسجيل تحذير"""
        try:
            log_message = f"[{context}] {message}" if context else message
            self.app_logger.warning(log_message)
        except Exception:
            pass
    
    def log_info(self, message: str, context: str = ""):
        """تسجيل معلومات"""
        try:
            log_message = f"[{context}] {message}" if context else message
            self.app_logger.info(log_message)
        except Exception:
            pass
    
    def log_sync(self, message: str, level: str = "info"):
        """تسجيل عملية مزامنة"""
        try:
            if level == "error":
                self.sync_logger.error(message)
                self.error_logger.error(f"[Sync] {message}")
            elif level == "warning":
                self.sync_logger.warning(message)
            else:
                self.sync_logger.info(message)
        except Exception:
            pass
    
    def get_error_logs(self, limit: int = 100) -> list:
        """الحصول على آخر الأخطاء"""
        try:
            if not ERROR_LOG_FILE.exists():
                return []
            
            logs = []
            with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # أخذ آخر limit سطر
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                for line in recent_lines:
                    if line.strip():
                        logs.append(line.strip())
            
            return logs
        except Exception:
            return []
    
    def get_app_logs(self, limit: int = 100) -> list:
        """الحصول على آخر Logs التطبيق"""
        try:
            if not APP_LOG_FILE.exists():
                return []
            
            logs = []
            with open(APP_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                for line in recent_lines:
                    if line.strip():
                        logs.append(line.strip())
            
            return logs
        except Exception:
            return []
    
    def clear_logs(self, log_type: str = "all"):
        """مسح الـ Logs"""
        try:
            if log_type == "all" or log_type == "error":
                if ERROR_LOG_FILE.exists():
                    ERROR_LOG_FILE.unlink()
                    self.error_logger.handlers.clear()
                    self.setup_loggers()
            
            if log_type == "all" or log_type == "app":
                if APP_LOG_FILE.exists():
                    APP_LOG_FILE.unlink()
                    self.app_logger.handlers.clear()
                    self.setup_loggers()
            
            if log_type == "all" or log_type == "sync":
                if SYNC_LOG_FILE.exists():
                    SYNC_LOG_FILE.unlink()
                    self.sync_logger.handlers.clear()
                    self.setup_loggers()
        except Exception:
            pass
    
    def get_log_file_size(self, log_type: str = "error") -> int:
        """الحصول على حجم ملف الـ Log"""
        try:
            if log_type == "error":
                return ERROR_LOG_FILE.stat().st_size if ERROR_LOG_FILE.exists() else 0
            elif log_type == "app":
                return APP_LOG_FILE.stat().st_size if APP_LOG_FILE.exists() else 0
            elif log_type == "sync":
                return SYNC_LOG_FILE.stat().st_size if SYNC_LOG_FILE.exists() else 0
            return 0
        except Exception:
            return 0


# Global logger instance
_logger_instance: Optional[EFMLogger] = None


def get_logger() -> EFMLogger:
    """الحصول على Logger العام"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EFMLogger()
    return _logger_instance


def log_error(error: Exception, context: str = "", additional_info: dict = None):
    """تسجيل خطأ (وظيفة مساعدة)"""
    get_logger().log_error(error, context, additional_info)


def log_warning(message: str, context: str = ""):
    """تسجيل تحذير (وظيفة مساعدة)"""
    get_logger().log_warning(message, context)


def log_info(message: str, context: str = ""):
    """تسجيل معلومات (وظيفة مساعدة)"""
    get_logger().log_info(message, context)


def log_sync(message: str, level: str = "info"):
    """تسجيل عملية مزامنة (وظيفة مساعدة)"""
    get_logger().log_sync(message, level)
