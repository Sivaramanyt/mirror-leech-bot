import os
import asyncio
import logging
from pyrogram import Client, filters
from aiohttp import web

# Configure MORE verbose logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Config
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

logger.info(f"🔧 Config loaded: API_ID={API_ID}, BOT_TOKEN={BOT_TOKEN[:10]}...")

# Create bot
bot = Client("terabox", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Health check
async def health(request):
    logger.info("🏥 Health check requested")
    return web.json_response({"status": "ok", "bot": "alive"})

async def start_health():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("✅ Health server started on port 8080")

# LOG EVERYTHING - This will catch ALL messages
@bot.on_message()
async def log_everything(client, message):
    logger.info(f"🔥 INCOMING MESSAGE: '{message.text}' from user {message.from_user.id} (@{message.from_user.username})")
    logger.info(f"🔥 Message type: {type(message).__name__}")
    logger.info(f"🔥 Chat ID: {message.chat.id}")
    logger.info(f"🔥 Message ID: {message.id}")

# Specific handlers
@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    logger.info(f"🚀 START COMMAND DETECTED from {message.from_user.id}")
    try:
        response = (
            "🎉 **SUCCESS! BOT IS WORKING!**\n\n"
            "✅ Message received and processed\n"
            "✅ Handlers are responding perfectly\n"
            "✅ Bot is fully operational\n\n"
            "Commands:\n"
            "• /ping - Test response\n"
            "• /test - Another test\n\n"
            "🚀 **Your bot is ALIVE!**"
        )
        await message.reply_text(response)
        logger.info("✅ START response sent successfully!")
    except Exception as e:
        logger.error(f"❌ START handler error: {e}")

@bot.on_message(filters.command("ping"))
async def ping_handler(client, message):
    logger.info(f"🏓 PING COMMAND DETECTED from {message.from_user.id}")
    try:
        await message.reply_text("🏓 **PONG!** Bot is alive! ⚡")
        logger.info("✅ PING response sent!")
    except Exception as e:
        logger.error(f"❌ PING handler error: {e}")

@bot.on_message(filters.command("test"))
async def test_handler(client, message):
    logger.info(f"🧪 TEST COMMAND DETECTED from {message.from_user.id}")
    try:
        await message.reply_text("🧪 **TEST SUCCESSFUL!** All systems working! 🎯")
        logger.info("✅ TEST response sent!")
    except Exception as e:
        logger.error(f"❌ TEST handler error: {e}")

async def main():
    try:
        logger.info("🚀 Starting ULTRA-DEBUG bot...")
        
        # Start health server
        await start_health()
        
        # Start bot
        await bot.start()
        me = await bot.get_me()
        logger.info(f"🤖 Bot info: @{me.username} (ID: {me.id})")
        logger.info(f"🎯 Bot is_bot: {me.is_bot}")
        logger.info(f"🔥 Bot first_name: {me.first_name}")
        
        logger.info("✅ Bot started and ready to receive messages!")
        logger.info("🔍 Send /start to test - watch the logs!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
            
