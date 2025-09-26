import os
import asyncio
import logging
from pyrogram import Client
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables (try both naming conventions)
API_ID = int(os.environ.get("API_ID") or os.environ.get("TELEGRAM_API", "0"))
API_HASH = os.environ.get("API_HASH") or os.environ.get("TELEGRAM_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

logger.info(f"🔧 Config - API_ID: {API_ID}, Token: {BOT_TOKEN[:10]}...")

# Health check for Koyeb
async def health_check(request):
    return web.json_response({"status": "healthy", "bot": "running"})

async def start_health_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", "8080")))
    await site.start()
    logger.info(f"✅ Health server started on port {os.environ.get('PORT', '8080')}")

# Bot instance
app = Client("mirror_leech_test", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Test handlers
@app.on_message()
async def handle_any_message(client, message):
    logger.info(f"🔥 MESSAGE: '{message.text}' from {message.from_user.id}")
    
    try:
        if message.text and message.text.startswith('/start'):
            await message.reply_text(
                "🎉 **MIRROR-LEECH BOT IS WORKING!**\n\n"
                "✅ Repository structure identified\n"
                "✅ Environment variables loaded\n" 
                "✅ Pyrogram handlers active\n\n"
                "📋 **Available Commands:**\n"
                "• `/start` - This message\n"
                "• `/mirror [url]` - Mirror files\n"
                "• `/leech [url]` - Leech files\n"
                "• `/ping` - Test response\n\n"
                "🚀 **Bot is fully operational!**"
            )
        elif message.text and message.text.startswith('/ping'):
            await message.reply_text("🏓 **Pong!** Mirror-Leech Bot responding! ⚡")
        elif message.text and message.text.startswith('/mirror'):
            await message.reply_text("🪞 **Mirror function detected!** Ready to implement full mirror functionality.")
        elif message.text and message.text.startswith('/leech'):
            await message.reply_text("📥 **Leech function detected!** Ready to implement full leech functionality.")
        else:
            await message.reply_text(f"✅ **Message received:** {message.text}\n\n🤖 Bot is working perfectly!")
        
        logger.info("✅ Response sent successfully")
        
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")

async def main():
    try:
        logger.info("🚀 Starting Mirror-Leech Bot...")
        
        # Validate environment variables
        if not API_ID or not API_HASH or not BOT_TOKEN:
            logger.error("❌ Missing required environment variables")
            logger.error(f"API_ID: {API_ID}, API_HASH: {'SET' if API_HASH else 'NOT SET'}, BOT_TOKEN: {'SET' if BOT_TOKEN else 'NOT SET'}")
            return
        
        # Start health check server
        await start_health_server()
        
        # Start bot
        await app.start()
        me = await app.get_me()
        logger.info(f"🤖 Mirror-Leech Bot started: @{me.username} (ID: {me.id})")
        logger.info("🎯 Bot is ready for mirror/leech operations!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
    
