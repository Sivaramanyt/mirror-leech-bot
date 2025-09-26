import os
import asyncio
import logging
from pyrogram import Client
from aiohttp import web

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
    return web.json_response({"status": "healthy", "timestamp": "2025-09-26"})

async def start_server():
    app = web.Application()
    app.router.add_get('/', health)
    app.router.add_get('/health', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("✅ Health server started on port 8080")

# Bot
bot = Client("fresh_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handler for ANY message
@bot.on_message()
async def handle_any_message(client, message):
    logger.info(f"🔥 MESSAGE: '{message.text}' from @{message.from_user.username} ({message.from_user.id})")
    
    try:
        if message.text and message.text.startswith('/start'):
            response = (
                "🎉 **FANTASTIC! NEW BOT IS WORKING!**\n\n"
                "✅ Fresh bot created successfully\n"
                "✅ Messages are being received\n"
                "✅ Handlers are responding perfectly\n"
                "✅ All systems operational\n\n"
                "🚀 **Commands available:**\n"
                "• `/start` - This message\n"
                "• `/ping` - Test response\n"
                "• `/test` - Another test\n"
                "• Any text message works!\n\n"
                "🎯 **Ready for Terabox downloads!**"
            )
        elif message.text and message.text.startswith('/ping'):
            response = "🏓 **PONG!** New bot is alive and kicking! ⚡"
        elif message.text and message.text.startswith('/test'):
            response = "🧪 **TEST SUCCESSFUL!** Everything working perfectly! 🎯"
        else:
            response = f"👋 **Hello!** I received your message: '{message.text}'\n\n✅ Bot is working great!"
        
        await message.reply_text(response)
        logger.info("✅ Response sent successfully!")
        
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")

async def main():
    try:
        logger.info("🚀 Starting FRESH bot...")
        
        # Start health server
        await start_server()
        
        # Start bot
        await bot.start()
        me = await bot.get_me()
        logger.info(f"🤖 NEW BOT READY: @{me.username} (ID: {me.id})")
        logger.info(f"🎯 Bot name: {me.first_name}")
        logger.info("✅ Send /start to test the new bot!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
            
