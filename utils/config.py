import os
import logging

logger = logging.getLogger(__name__)

# Get environment variables - Telegram Bot
API_ID = int(os.environ.get("API_ID") or os.environ.get("TELEGRAM_API", "0"))
API_HASH = os.environ.get("API_HASH") or os.environ.get("TELEGRAM_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
PORT = int(os.environ.get("PORT", "8080"))

# Database Configuration - ADDED
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "terabox_bot")

# MongoDB Atlas example: DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/
# Local MongoDB example: DATABASE_URL=mongodb://localhost:27017/

# Terabox API configuration
TERABOX_API_BASE = "https://www.terabox.com/api/shorturlinfo"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0'
}

# Supported domains
TERABOX_DOMAINS = [
    'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
    'momerybox.com', 'teraboxapp.com', '1024tera.com', 'gibibox.com',
    'goaibox.com', 'terasharelink.com'
]

# Bot Configuration
MAX_FILE_SIZE = 2147483648  # 2GB
DOWNLOAD_DIRECTORY = "downloads"
CONCURRENT_DOWNLOADS = 3

# Rate Limiting
API_RATE_LIMIT = 10  # requests per minute
API_TIMEOUT = 30  # seconds

# Features toggle
FEATURES = {
    "database_enabled": bool(DATABASE_URL),
    "system_stats": True,
    "enhanced_logging": True,
    "rate_limiting": True,
    "file_type_detection": True,
    "progress_tracking": True
}

def validate_environment():
    """Validate required environment variables"""
    if not API_ID or not API_HASH or not BOT_TOKEN:
        logger.error("❌ Missing required environment variables")
        logger.error(f"API_ID: {API_ID}, API_HASH: {'SET' if API_HASH else 'NOT SET'}, BOT_TOKEN: {'SET' if BOT_TOKEN else 'NOT SET'}")
        return False
    
    # Log database status
    if DATABASE_URL:
        logger.info("✅ Database URL configured")
    else:
        logger.warning("⚠️ Database URL not configured - running without database")
    
    return True

def get_database_config():
    """Get database configuration"""
    return {
        "url": DATABASE_URL,
        "name": DATABASE_NAME,
        "enabled": bool(DATABASE_URL)
}
        
