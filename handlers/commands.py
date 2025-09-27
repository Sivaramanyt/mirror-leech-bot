import time
import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import validators

logger = logging.getLogger(__name__)

def setup_command_handlers(app):
    """Setup command handlers - PROPER STRUCTURE"""
    
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
        """Enhanced leech command with Terabox URL analysis"""
        try:
            user_id = message.from_user.id
            
            if len(message.command) < 2:
                await message.reply_text(
                    "❌ **Please provide a URL to download**\n\n"
                    "**Usage:** `/leech [URL]`\n"
                    "**Examples:**\n"
                    "• `/leech https://terabox.com/s/abc123`\n"
                    "• `/leech https://nephobox.com/s/xyz789`\n\n"
                    "🔗 **Supported:** All Terabox variants"
                )
                return
            
            url = " ".join(message.command[1:])
            
            if not validators.url(url):
                await message.reply_text("❌ **Invalid URL format**\n\nPlease provide a valid URL starting with http:// or https://")
                return
            
            # Check if it's a supported Terabox URL
            supported_domains = [
                'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
                'momerybox.com', 'teraboxapp.com', '1024tera.com', 'gibibox.com',
                'goaibox.com', 'terasharelink.com'
            ]
            
            is_terabox = any(domain in url.lower() for domain in supported_domains)
            
            # Processing message with enhanced analysis
            status_msg = await message.reply_text("🔍 **Analyzing URL...**")
            
            if is_terabox:
                # Extract surl from URL
                import re
                surl_pattern = r'/s/([a-zA-Z0-9_-]+)'
                surl_match = re.search(surl_pattern, url)
                
                if surl_match:
                    surl = surl_match.group(1)
                    await status_msg.edit_text(
                        f"✅ **Terabox URL Detected!**\n\n"
                        f"🔗 **Platform:** Terabox Family\n"
                        f"📎 **URL:** `{url[:50]}{'...' if len(url) > 50 else ''}`\n"
                        f"🔑 **Share Code:** `{surl}`\n"
                        f"✅ **Status:** Valid format detected\n\n"
                        f"🚀 **Ready for download!**\n"
                        f"🔧 **Next:** File info extraction will be added next.\n\n"
                        f"**This confirms Terabox URL parsing is working!** ✅"
                    )
                else:
                    await status_msg.edit_text(
                        f"❌ **Invalid Terabox URL Format**\n\n"
                        f"Terabox URLs should contain `/s/` followed by share code.\n"
                        f"**Example:** `https://terabox.com/s/abc123xyz`"
                    )
            else:
                await status_msg.edit_text(
                    f"⚠️ **URL Not Supported Yet**\n\n"
                    f"🔗 **URL:** `{url[:50]}{'...' if len(url) > 50 else ''}`\n\n"
                    f"**Currently supported:**\n"
                    f"• terabox.com\n"
                    f"• nephobox.com  \n"
                    f"• 4funbox.com\n"
                    f"• mirrobox.com\n"
                    f"• And 6 more variants\n\n"
                    f"Try with a Terabox family URL!"
                )
            
            logger.info(f"📥 Enhanced leech processed for user {user_id} - Terabox: {is_terabox}")
            
        except Exception as e:
            logger.error(f"❌ Leech command error: {e}")
            await message.reply_text(
                "❌ **Error occurred**\n\n"
                "Please try again or contact support."
            )
    
    logger.info("✅ All command handlers setup complete - minimal working version")
            
