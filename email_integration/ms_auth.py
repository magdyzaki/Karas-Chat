# Microsoft Authentication
import os
import pickle

try:
    import msal
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False
    msal = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

from .ms_config import CLIENT_ID, AUTHORITY, SCOPES, TOKEN_CACHE_PATH


def _load_cache(cache_path=None):
    """تحميل token cache من مسار محدد أو المسار الافتراضي"""
    if not MSAL_AVAILABLE:
        return None
        
    if cache_path is None:
        cache_path = TOKEN_CACHE_PATH
    
    cache = msal.SerializableTokenCache()
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                cache.deserialize(pickle.load(f))
        except:
            pass
    return cache


def _save_cache(cache, cache_path=None):
    """حفظ token cache في مسار محدد أو المسار الافتراضي"""
    if not MSAL_AVAILABLE or not cache:
        return
        
    if cache_path is None:
        cache_path = TOKEN_CACHE_PATH
    
    if cache.has_state_changed:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(cache.serialize(), f)
        except:
            pass


def acquire_token_interactive(cache_path=None):
    """الحصول على token تفاعلي (للاستخدام مع الحساب الافتراضي)"""
    if not MSAL_AVAILABLE:
        raise RuntimeError("msal library is not installed. Please install it: pip install msal")
    
    cache = _load_cache(cache_path)
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            _save_cache(cache, cache_path)
            return result["access_token"]

    # أول مرة: نافذة تسجيل دخول Microsoft
    result = app.acquire_token_interactive(scopes=SCOPES)
    if "access_token" in result:
        _save_cache(cache, cache_path)
        return result["access_token"]

    raise RuntimeError(f"OAuth failed: {result}")


def get_account_email(access_token):
    """الحصول على البريد الإلكتروني للحساب من Microsoft Graph"""
    if not REQUESTS_AVAILABLE:
        return None
        
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("mail") or data.get("userPrincipalName")
    except:
        pass
    return None
