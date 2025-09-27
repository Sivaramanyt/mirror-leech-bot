import logging
import time
from datetime import datetime
from pyrogram import Client
from aiohttp import web
import psutil
import colorlog
from .config import API_ID, API_HASH, BOT_TOKEN, PORT

def setup_logging():
    """Setup enhanced logging with colors"""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    ))
    
    logger = colorlog.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def create_bot():
    """Create and return bot instance"""
    return Client("terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def health_check(request):
    """Enhanced health check with system stats"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return web.json_response({
        "status": "healthy",
        "bot": "TeraboxLeechBot",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "memory_usage": f"{memory.percent}%",
            "cpu_usage": f"{cpu_percent}%",
            "available_memory": f"{memory.available / (1024**3):.2f} GB"
        }
    })

async def start_health_server():
    """Start health check server"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/stats', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger = logging.getLogger(__name__)
    logger.info("✅ Health server started with system monitoring")
