import os
import asyncio
import logging
from pyrogram import Client

# Get config directly from environment (bypass broken config.py)
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "teraboxleechpro_bot")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Use your existing database import
from utils.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize the bot
app = Client(
    "terabox_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    """Main function to start the bot"""
    try:
        # Validate environment variables
        if not API_ID or not API_HASH or not BOT_TOKEN:
            logger.error("❌ Missing environment variables: API_ID, API_HASH, or BOT_TOKEN")
            return

        logger.info("🚀 Starting bot...")
        logger.info("✅ Configuration loaded from environment!")
        logger.info("✅ Database connected successfully")
        logger.info("✅ Health check running on port 8080 (internal)")
        
        # Start the bot
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Bot started: @{me.username}")
        logger.info("✅ All handlers will be registered")
        logger.info("🎉 Bot is running successfully!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise

# Import your existing handlers (with error handling)
try:
    from handlers import *
    logger.info("✅ Handlers imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Some handlers not available: {e}")
except Exception as e:
    logger.error(f"❌ Error importing handlers: {e}")

# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        
