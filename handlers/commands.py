import time
import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import validators

logger = logging.getLogger(__name__)

def setup_command_handlers(app):
    """Setup command handlers - minimal working version"""
    
    @app.on_message(filters.command("start"))
    async def start_command(client, message: Message):
        start_text = f"""
🚀 **Welcome to Terabox Leech Bot!**

Hello {message.from_user.mention}! 👋

📋 **Commands:**
• `/leech [url]` - Download from Terabox
• `/help` - Show help
• `/ping` - Test bot

🔗 **Supported:** All Terabox variants

Ready for downloads! 🚀
        """
        
        keyboard = [[
            InlineKeyboardButton("📋 Help", callback_data="help"),
            InlineKeyboardButton("🏓 Ping", callback_data="ping")
        ]]
        
        await message.reply_text(start_text, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"📥 Start command from user {message.from_user.id}")

    @app.on_message(filters.command("ping"))
    async def ping_command(client, message: Message):
        start_time = time.time()
        msg = await message.reply_text("🏓 Pinging...")
        ping_time = round((time.time() - start_time) * 1000, 2)
        await msg.edit_text(f"🏓 **Pong!** {ping_time}ms")

    @app.on_message(filters.command("help"))
    async def help_command(client, message: Message):
        await message.reply_text("""
❓ **Terabox Leech Bot Help**

📥 **Usage:**
• `/leech [url]` - Download from Terabox
• Send Terabox URL directly

🔗 **Supported:**
• terabox.com, nephobox.com
• 4funbox.com, mirrobox.com
• All Terabox variants

🚀 **Ready to download!**
        """)

    @app.on_message(filters.command("leech"))
    async def leech_command(client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a URL\n\nUsage: `/leech [url]`")
            return
            
        url = " ".join(message.command[1:])
        
        if not validators.url(url):
            await message.reply_text("❌ Invalid URL format")
            return
            
        await message.reply_text(f"✅ **Leech Command Working!**\n\nURL: {url[:50]}...\n\nBot is responding correctly! 🚀")
        logger.info(f"📥 Leech command processed for user {message.from_user.id}")
    
    logger.info("✅ All command handlers setup complete - minimal working version")
        
