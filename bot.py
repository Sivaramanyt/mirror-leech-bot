import os
import asyncio
import logging
from pyrogram import Client
from aiohttp import web
import aiohttp

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

logger.info(f"🔧 Using token: {BOT_TOKEN[:15]}...")

# Health check
async def health(request):
    return web.json_response({"status": "healthy"})

async def start_server():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("✅ Health server started")

async def delete_webhook():
    """Delete any existing webhook that might be blocking messages"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as response:
                result = await response.json()
                logger.info(f"🔧 Webhook deletion result: {result}")
                
        # Also try getWebhookInfo to see current status
        info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        async with aiohttp.ClientSession() as session:
            async with session.get(info_url) as response:
                info = await response.json()
                logger.info(f"🔧 Current webhook info: {info}")
                
    except Exception as e:
        logger.error(f"❌ Webhook deletion error: {e}")

# Bot
bot = Client("clean_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handler for ANY message
@bot.on_message()
async def handle_any_message(client, message):
    logger.info(f"🔥🔥🔥 MESSAGE RECEIVED: '{message.text}' from {message.from_user.id}")
    
    try:
        if message.text and message.text.startswith('/start'):
            response = "🎉 **WEBHOOK DELETED! BOT IS NOW WORKING!** ✅"
        else:
            response = f"✅ Message received: {message.text}"
        
        await message.reply_text(response)
        logger.info("🔥🔥🔥 RESPONSE SENT!")
        
    except Exception as e:
        logger.error(f"❌ Response error: {e}")

async def main():
    try:
        logger.info("🚀 Starting bot with webhook cleanup...")
        
        # Start health server
        await start_server()
        
        # DELETE ANY EXISTING WEBHOOK FIRST
        await delete_webhook()
        logger.info("🔧 Webhook cleanup completed")
        
        # Start bot
        await bot.start()
        me = await bot.get_me()
        logger.info(f"🤖 BOT: @{me.username} (Clean start)")
        logger.info("🎯 Webhook deleted - bot should now receive messages!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
            
