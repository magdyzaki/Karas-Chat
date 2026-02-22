# Microsoft Graph API Configuration
# يمكن تعديل هذه القيم حسب الحاجة

CLIENT_ID = "604b38cf-0315-4242-8fed-4663296add78"
TENANT_ID = "3fa34c50-dcdd-43be-b9f2-088f4a99a01e"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Mail.Read", "User.Read"]

# مكان حفظ التوكن محليًا (آمن)
TOKEN_CACHE_PATH = "database/ms_token_cache.bin"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TARGET_FOLDER_NAME = "EFM_Clients"
