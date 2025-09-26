import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from aiohttp import web
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
API_ID = int(os.environ.get("API_ID") or os.environ.get("TELEGRAM_API", "0"))
API_HASH = os.environ.get("API_HASH") or os.environ.get("TELEGRAM_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

logger.info(f"🔧 Starting bot with API_ID: {API_ID}")

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
    logger.info("✅ Health server started")

# Bot instance
app = Client("terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Basic handlers
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_mention = message.from_user.mention
    start_text = f"""
🚀 **Welcome to Lightning-Fast Terabox Leech Bot!**

Hello {user_mention}! 👋

⚡ **Lightning-fast downloads** from Terabox
🔒 **Secure and private** file handling  
🎯 **Professional-grade** performance
📱 **Original filenames** preserved

📋 **Available Commands:**
• `/leech [url]` - Download from Terabox
• `/status` - Check download status  
• `/cancel` - Cancel active download
• `/help` - Get detailed help
• `/ping` - Check bot response

🔗 **Supported Links:**
• Terabox, Nephobox, 4funbox
• Mirrobox, Momerybox, Teraboxapp
• 1024tera, Gibibox, Goaibox

🚀 **Ready for lightning-fast downloads!**

Use `/leech [your_terabox_url]` to get started!
    """
    await message.reply_text(start_text)

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    await message.reply_text("🏓 **Pong!** Bot is online and working! ⚡")

@app.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = """
❓ **HELP - How to Use the Bot**

📥 **Download Files:**
• Send `/leech [terabox_url]` to download
• Example: `/leech https://terabox.com/s/abc123`

⚡ **Features:**
• Lightning-fast downloads
• Original filenames preserved
• Progress tracking
• Secure and private

📱 **Commands:**
• `/leech [url]` - Download from URL
• `/status` - Check download status
• `/cancel` - Cancel active download  
• `/help` - Show this help
• `/ping` - Check bot response

🔗 **Supported Domains:**
• terabox.com, nephobox.com
• 4funbox.com, mirrobox.com
• And other Terabox variants

🚀 **Ready to download? Use `/leech [url]`!**
    """
    await message.reply_text(help_text)

async def main():
    try:
        logger.info("🚀 Starting Terabox Leech Bot...")
        
        # Start health server
        await start_health_server()
        
        # Start bot
        await app.start()
        me = await app.get_me()
        logger.info(f"🤖 Bot started: @{me.username} (ID: {me.id})")
        logger.info("🎯 Bot is ready for downloads!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
                
