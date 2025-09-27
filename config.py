import os
from typing import List, Dict, Any

# Bot configuration
API_ID = int(os.environ.get("API_ID") or os.environ.get("TELEGRAM_API", "0"))
API_HASH = os.environ.get("API_HASH") or os.environ.get("TELEGRAM_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Owner configuration
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
ADMINS = [OWNER_ID] if OWNER_ID else []

# Bot settings
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
MAX_FILE_SIZE = 2147483648  # 2GB
DOWNLOAD_DIRECTORY = "downloads"
CONCURRENT_DOWNLOADS = 3

# Server configuration
PORT = int(os.environ.get("PORT", "8080"))
HOST = "0.0.0.0"

# API Rate limiting
API_RATE_LIMIT = 10  # requests per minute
API_TIMEOUT = 30  # seconds

# Supported Terabox domains
SUPPORTED_DOMAINS: List[str] = [
    "terabox.com",
    "nephobox.com", 
    "4funbox.com",
    "mirrobox.com",
    "momerybox.com",
    "teraboxapp.com",
    "1024tera.com",
    "gibibox.com",
    "goaibox.com",
    "terasharelink.com"
]

# File type categories
FILE_TYPES: Dict[str, List[str]] = {
    "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"],
    "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "executable": [".exe", ".apk", ".deb", ".rpm", ".dmg", ".msi"]
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Features toggle
FEATURES: Dict[str, bool] = {
    "system_stats": True,
    "enhanced_logging": True,
    "rate_limiting": True,
    "file_type_detection": True,
    "thumbnail_support": True,
    "progress_tracking": True
}
