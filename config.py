# Mirror Leech Bot Configuration
import os
from typing import Dict, List, Optional

# Required Variables
BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
OWNER_ID: int = int(os.environ.get("OWNER_ID", "0"))
TELEGRAM_API: int = int(os.environ.get("TELEGRAM_API", "0"))
TELEGRAM_HASH: str = os.environ.get("TELEGRAM_HASH", "")

# Database
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

# Optional Variables
AUTHORIZED_CHATS: str = os.environ.get("AUTHORIZED_CHATS", "")
SUDO_USERS: str = os.environ.get("SUDO_USERS", "")

# Upload Settings
DEFAULT_UPLOAD: str = os.environ.get("DEFAULT_UPLOAD", "tg")  # tg or gd
GDRIVE_ID: str = os.environ.get("GDRIVE_ID", "")
IS_TEAM_DRIVE: bool = os.environ.get("IS_TEAM_DRIVE", "False").lower() == "true"

# Leech Settings
LEECH_SPLIT_SIZE: int = int(os.environ.get("LEECH_SPLIT_SIZE", str(2 * 1024 * 1024 * 1024)))  # 2GB
AS_DOCUMENT: bool = os.environ.get("AS_DOCUMENT", "False").lower() == "true"
LEECH_DUMP_CHAT: str = os.environ.get("LEECH_DUMP_CHAT", "")

# Status Settings
STATUS_UPDATE_INTERVAL: int = int(os.environ.get("STATUS_UPDATE_INTERVAL", "10"))
STATUS_LIMIT: int = int(os.environ.get("STATUS_LIMIT", "4"))

# Queue Settings
QUEUE_ALL: int = int(os.environ.get("QUEUE_ALL", "8"))
QUEUE_DOWNLOAD: int = int(os.environ.get("QUEUE_DOWNLOAD", "4"))
QUEUE_UPLOAD: int = int(os.environ.get("QUEUE_UPLOAD", "4"))

# File Settings
EXCLUDED_EXTENSIONS: str = os.environ.get("EXCLUDED_EXTENSIONS", "")
MAX_FILE_SIZE: int = int(os.environ.get("MAX_FILE_SIZE", str(2 * 1024 * 1024 * 1024)))  # 2GB for free tier

# Health Check (for Koyeb)
PORT: int = int(os.environ.get("PORT", "8000"))

# Google Drive Service Accounts
USE_SERVICE_ACCOUNTS: bool = os.environ.get("USE_SERVICE_ACCOUNTS", "False").lower() == "true"

# Commands
CMD_SUFFIX: str = os.environ.get("CMD_SUFFIX", "")

# Validation
def validate_config():
    """Validate required configuration"""
    required_vars = ["BOT_TOKEN", "OWNER_ID", "TELEGRAM_API", "TELEGRAM_HASH"]
    missing_vars = []

    for var in required_vars:
        if not globals().get(var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    print("✅ Configuration validated successfully!")
    return True

# Parse authorized chats and sudo users
def parse_ids(ids_str: str) -> List[int]:
    """Parse comma/space separated IDs"""
    if not ids_str:
        return []

    ids = []
    for id_str in ids_str.replace(',', ' ').split():
        try:
            ids.append(int(id_str))
        except ValueError:
            continue
    return ids

AUTHORIZED_CHATS_LIST = parse_ids(AUTHORIZED_CHATS)
SUDO_USERS_LIST = parse_ids(SUDO_USERS)
EXCLUDED_EXTENSIONS_LIST = EXCLUDED_EXTENSIONS.split() if EXCLUDED_EXTENSIONS else []

# Add owner to authorized users
if OWNER_ID and OWNER_ID not in SUDO_USERS_LIST:
    SUDO_USERS_LIST.append(OWNER_ID)
