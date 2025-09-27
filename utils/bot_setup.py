import logging
from datetime import datetime
from pyrogram import Client
from aiohttp import web
from .config import API_ID, API_HASH, BOT_TOKEN, PORT

def setup_logging():
    """Simple logging setup"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_bot():
    """Create bot instance"""
    return Client("terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def health_check(request):
    """Simple health check - no psutil needed"""
    return web.json_response({
        "status": "healthy",
        "bot": "TeraboxBot",
        "timestamp": datetime.now().isoformat(),
        "message": "Bot is running successfully"
    })

async def start_health_server():
    """Start health server"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Health server started on port {PORT}")
    
