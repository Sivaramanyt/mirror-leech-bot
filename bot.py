import os
import asyncio
import logging
from pyrogram import Client
from aiohttp import web

# Get config from environment
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "teraboxleechpro_bot")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

from utils.database import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Client("terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def health_check(request):
    """Health check endpoint for Koyeb"""
    return web.json_response({"status": "healthy", "bot": "running", "timestamp": "2025-09-26"})

async def start_health_server():
    """Start health check server"""
    app_web = web.Application()
    app_web.router.add_get('/', health_check)
    app_web.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("✅ Health check server started on port 8080")

async def main():
    try:
        if not API_ID or not API_HASH or not BOT_TOKEN:
            logger.error("❌ Missing environment variables")
            return

        logger.info("🚀 Starting bot...")
        logger.info("✅ Configuration loaded from environment!")
        logger.info("✅ Database connected successfully")
        
        # Start health check server
        await start_health_server()
        
        # Start the bot
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Bot started: @{me.username}")
        logger.info("✅ All handlers registered")
        logger.info("🎉 Bot is running successfully and healthy!")
        
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise

# Import handlers
try:
    from handlers import *
    logger.info("✅ Handlers imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Some handlers not available: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
