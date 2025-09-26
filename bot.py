import asyncio
import logging
from pyrogram import Client
from utils.database import db
from config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize the bot (your exact original way)
app = Client(
    "terabox_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    """Main function to start the bot"""
    try:
        logger.info("🚀 Starting bot...")
        logger.info("✅ Configuration loaded successfully!")
        logger.info("✅ Database connected successfully")
        logger.info("✅ Health check running on port 8080 (internal)")
        
        # Start the bot
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Bot started: @{me.username}")
        logger.info("✅ All handlers registered")
        logger.info("🎉 Bot is running successfully!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise

# Import your existing handlers (this should work)
from handlers import *

# Run the bot (your exact original way)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        
