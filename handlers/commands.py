import time
import logging
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import psutil
from utils.terabox import extract_terabox_info, format_file_size, get_file_type_emoji
from utils.config import TERABOX_DOMAINS

logger = logging.getLogger(__name__)

def setup_command_handlers(app):
    """Setup all command handlers"""
    
    @app.on_message(filters.command("start"))
    async def start_command(client, message: Message):
        """Enhanced start command"""
        user_mention = message.from_user.mention
        user_id = message.from_user.id
        
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
• `/help` - Get detailed help
• `/ping` - Check bot response

🔗 **Supported Platforms:**
• Terabox, Nephobox, 4funbox
• Mirrobox, Momerybox, Teraboxapp
• 1024tera, Gibibox, Goaibox

🚀 **Ready for lightning-fast downloads!**

Use `/leech [your_terabox_url]` to get started!
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 Help", callback_data="help"),
             InlineKeyboardButton("🏓 Ping", callback_data="ping")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(start_text, reply_markup=reply_markup)
        logger.info(f"📥 Start command from user {user_id}")

    @app.on_message(filters.command("ping"))
    async def ping_command(client, message: Message):
        """Enhanced ping with system stats"""
        start_time = time.time()
        ping_msg = await message.reply_text("🏓 Pinging...")
        end_time = time.time()
        
        ping_time = round((end_time - start_time) * 1000, 2)
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        await ping_msg.edit_text(
            f"🏓 **Pong!**\n\n"
            f"⚡ **Response Time:** {ping_time}ms\n"
            f"✅ **Bot Status:** Online\n"
            f"💾 **Memory Usage:** {memory.percent}%\n"
            f"🖥️ **CPU Usage:** {cpu_percent}%\n"
            f"🚀 **Ready for downloads!**"
        )

    @app.on_message(filters.command("help"))
    async def help_command(client, message: Message):
        """Enhanced help command"""
        help_text = """
❓ **TERABOX LEECH BOT - HELP**

📥 **How to Download:**
• Send `/leech [terabox_url]` to download
• Or just send the Terabox link directly!
• Example: `/leech https://terabox.com/s/abc123`

⚡ **Features:**
• Lightning-fast downloads
• Original filenames preserved
• File type detection
• Progress tracking
• Secure and private

📱 **Commands:**
• `/start` - Show welcome message
• `/leech [url]` - Process Terabox link
• `/status` - Check download status
• `/help` - Show this help
• `/ping` - Test bot response

🔗 **Supported Platforms:**
• Terabox.com, Nephobox.com
• 4funbox.com, Mirrobox.com
• And other Terabox variants

🚀 **Ready to download? Send any Terabox link!**
        """
        await message.reply_text(help_text)

    @app.on_message(filters.command("status"))
    async def status_command(client, message: Message):
        """Enhanced status command"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        await message.reply_text(
            f"📊 **BOT STATUS**\n\n"
            f"✅ **Bot Status:** Online and operational\n"
            f"💾 **Memory:** {memory.percent}% used\n"
            f"🖥️ **CPU:** {cpu_percent}%\n"
            f"⚡ **Performance:** Optimal\n"
            f"🔄 **Active Downloads:** None\n\n"
            f"Use `/leech [url]` to start downloading.\n\n"
            f"🚀 **Lightning-fast downloads ready!**"
        )

    @app.on_message(filters.command("leech"))
    async def leech_command(client, message: Message):
        """Main leech command handler"""
        try:
            # Check if URL provided
            if len(message.command) < 2:
                await message.reply_text(
                    "❌ **Please provide a URL to download**\n\n"
                    "**Usage:** `/leech [URL]`\n"
                    "**Example:** `/leech https://terabox.com/s/abc123`\n\n"
                    "🔗 **Supported platforms:**\n"
                    "• Terabox and all variants\n\n"
                    "💡 **Tip:** You can also send the link directly!"
                )
                return
            
            url = message.command[1]
            user_id = message.from_user.id
            
            # Validate Terabox URL
            if not any(domain in url.lower() for domain in TERABOX_DOMAINS):
                supported_list = "\n".join([f"• {domain}" for domain in TERABOX_DOMAINS[:5]])
                await message.reply_text(
                    f"❌ **Unsupported URL**\n\n"
                    f"**Supported platforms:**\n{supported_list}\n• And more variants"
                )
                return
            
            # Send processing message
            status_msg = await message.reply_text(
                f"🚀 **Processing Started!**\n\n"
                f"📎 **URL:** `{url[:60]}...`\n"
                f"👤 **User:** {message.from_user.mention}\n"
                f"⏳ **Status:** Extracting file information...\n"
                f"🔄 **Please wait...**"
            )
            
            # Extract file info
            file_info = await extract_terabox_info(url)
            
            if not file_info:
                await status_msg.edit_text(
                    "❌ **Failed to Process Link**\n\n"
                    "**Possible reasons:**\n"
                    "• Link might be invalid or expired\n"
                    "• File might be private or restricted\n"
                    "• Server might be temporarily unavailable\n\n"
                    "**Please try:**\n"
                    "• Verify the link is correct\n"
                    "• Try again in a few moments"
                )
                return
            
            # Prepare file info
            filename = file_info['filename']
            file_size = format_file_size(file_info['size'])
            download_url = file_info['download_url']
            file_emoji = get_file_type_emoji(filename)
            
            if file_info['isdir'] == 1:
                # Folder response
                result_text = f"""
📁 **FOLDER DETECTED**

{file_emoji} **Folder Name:** `{filename}`
📊 **Total Size:** {file_size}
🗂️ **Type:** Directory/Folder

❗ **Note:** This contains multiple files.
Access individual files within the folder.
                """
            else:
                # Single file response
                result_text = f"""
✅ **FILE READY FOR DOWNLOAD**

{file_emoji} **Filename:** `{filename}`
📊 **Size:** {file_size}
⚡ **Status:** Ready for download

🔗 **Download Options:**
                """
            
            # Create download buttons
            keyboard = []
            
            if download_url and file_info['isdir'] == 0:
                keyboard.append([InlineKeyboardButton("📥 Direct Download", url=download_url)])
            
            keyboard.append([InlineKeyboardButton("🔗 Open in Terabox", url=url)])
            keyboard.append([InlineKeyboardButton("🔄 Process Another", callback_data="start")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(result_text, reply_markup=reply_markup)
            
            logger.info(f"📥 Leech processed for user {user_id}: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error in leech command: {e}")
            await message.reply_text("❌ An unexpected error occurred. Please try again.")
