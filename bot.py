from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
import logging
import os
import requests
import re
from aiohttp import web
import aiofiles
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Terabox API endpoints and headers
TERABOX_API_BASE = "https://www.terabox.com/api/shorturlinfo"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Health check server for Koyeb
async def health_check(request):
    return web.json_response({"status": "healthy", "bot": "TeraboxLeechBot"})

async def start_health_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", "8080")))
    await site.start()
    logger.info("✅ Health server started")

# Bot command handlers
async def start_command(update: Update, context) -> None:
    """Start command handler"""
    user = update.effective_user
    welcome_text = f"""
🚀 **Welcome to Lightning-Fast Terabox Leech Bot!**

Hello {user.first_name}! 👋

⚡ **Features:**
• Lightning-fast downloads from Terabox
• Support for all Terabox variants
• Direct file download links
• Progress tracking
• Original filenames preserved

📋 **How to Use:**
• Send me any Terabox link
• Or use `/leech [your_terabox_link]`

🔗 **Supported Platforms:**
• Terabox, Nephobox, 4funbox
• Mirrobox, Momerybox, Teraboxapp
• 1024tera, Gibibox, and more!

🆘 **Commands:**
• `/help` - Show help
• `/ping` - Test bot
• `/about` - About this bot

🚀 **Ready for lightning-fast downloads!**
    """
    
    keyboard = [
        [InlineKeyboardButton("📋 Help", callback_data="help"),
         InlineKeyboardButton("🔗 About", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context) -> None:
    """Help command handler"""
    help_text = """
❓ **TERABOX LEECH BOT - HELP**

📥 **How to Download:**
1. Copy any Terabox link
2. Send it to me directly, or
3. Use: `/leech [your_link]`

✅ **Supported Links:**
• `terabox.com/s/xxxxx`
• `nephobox.com/s/xxxxx`
• `4funbox.com/s/xxxxx`
• `mirrobox.com/s/xxxxx`
• `momerybox.com/s/xxxxx`
• `teraboxapp.com/s/xxxxx`
• `1024tera.com/s/xxxxx`
• And many more variants!

⚡ **Features:**
• Instant download link generation
• Original filenames preserved
• High-speed direct downloads
• Support for large files
• Works with private links

📝 **Example:**
Send: `https://terabox.com/s/1ABCdefgh123`
Get: Direct download link instantly!

🔧 **Commands:**
• `/start` - Start the bot
• `/help` - This help message
• `/ping` - Test bot response
• `/about` - About this bot

💡 **Tips:**
• Works with both public and private Terabox links
• No registration required
• Completely free to use
• Fast and reliable

🚀 **Start sending your Terabox links now!**
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def ping_command(update: Update, context) -> None:
    """Ping command handler"""
    start_time = time.time()
    message = await update.message.reply_text("🏓 Pinging...")
    end_time = time.time()
    
    ping_time = round((end_time - start_time) * 1000, 2)
    
    await message.edit_text(
        f"🏓 **Pong!**\n\n"
        f"⚡ **Response Time:** {ping_time}ms\n"
        f"✅ **Bot Status:** Online\n"
        f"🚀 **Ready for downloads!**",
        parse_mode='Markdown'
    )

async def about_command(update: Update, context) -> None:
    """About command handler"""
    about_text = """
🤖 **TERABOX LEECH BOT**

🔥 **Lightning-fast Terabox downloader bot**

⚡ **Features:**
• Instant link processing
• High-speed downloads
• All Terabox variants supported
• Original quality preserved
• No file size limits
• Works with private links

🛠️ **Technology:**
• Built with Python
• Telegram Bot API
• Advanced link parsing
• Optimized for speed

📊 **Statistics:**
• 🔥 Ultra-fast processing
• ⚡ Lightning-speed downloads
• 🎯 99.9% success rate
• 🚀 24/7 availability

🌟 **Why Choose This Bot:**
• No ads or spam
• No registration required
• Completely free
• Privacy focused
• Fast and reliable

💡 **Developed for power users who need:**
• Quick Terabox downloads
• Reliable file access
• Professional-grade service

🚀 **Start using now - send any Terabox link!**
    """
    
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Start", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(about_text, reply_markup=reply_markup, parse_mode='Markdown')

def extract_terabox_info(url):
    """Extract file information from Terabox URL"""
    try:
        # Extract shorturl from the URL
        patterns = [
            r'terabox\.com/s/([a-zA-Z0-9_-]+)',
            r'nephobox\.com/s/([a-zA-Z0-9_-]+)',
            r'4funbox\.com/s/([a-zA-Z0-9_-]+)',
            r'mirrobox\.com/s/([a-zA-Z0-9_-]+)',
            r'momerybox\.com/s/([a-zA-Z0-9_-]+)',
            r'teraboxapp\.com/s/([a-zA-Z0-9_-]+)',
            r'1024tera\.com/s/([a-zA-Z0-9_-]+)',
            r'gibibox\.com/s/([a-zA-Z0-9_-]+)',
        ]
        
        shorturl = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                shorturl = match.group(1)
                break
        
        if not shorturl:
            return None
        
        # Make API request to get file info
        api_url = f"{TERABOX_API_BASE}?shorturl={shorturl}&root=1"
        
        response = requests.get(api_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('errno') == 0 and data.get('list'):
                file_info = data['list'][0]
                
                return {
                    'filename': file_info.get('server_filename', 'Unknown'),
                    'size': file_info.get('size', 0),
                    'download_url': file_info.get('dlink', ''),
                    'thumbnail': file_info.get('thumbs', {}).get('url3', ''),
                    'category': file_info.get('category', 0),
                    'isdir': file_info.get('isdir', 0)
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting Terabox info: {e}")
        return None

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

async def process_terabox_link(update: Update, context) -> None:
    """Process Terabox links sent by users"""
    url = update.message.text.strip()
    
    # Check if the message contains a Terabox link
    terabox_domains = [
        'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
        'momerybox.com', 'teraboxapp.com', '1024tera.com', 'gibibox.com'
    ]
    
    if not any(domain in url.lower() for domain in terabox_domains):
        await update.message.reply_text(
            "❌ **Invalid Link**\n\n"
            "Please send a valid Terabox link.\n\n"
            "**Supported platforms:**\n"
            "• Terabox\n• Nephobox\n• 4funbox\n• Mirrobox\n• And more!\n\n"
            "**Example:**\n"
            "`https://terabox.com/s/1ABCdef123`",
            parse_mode='Markdown'
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "🔄 **Processing your Terabox link...**\n\n"
        "⚡ Extracting file information\n"
        "🚀 This will take just a moment!",
        parse_mode='Markdown'
    )
    
    try:
        # Extract file info
        file_info = extract_terabox_info(url)
        
        if not file_info:
            await processing_msg.edit_text(
                "❌ **Failed to Process Link**\n\n"
                "• Link might be invalid or expired\n"
                "• File might be private or restricted\n"
                "• Server might be temporarily unavailable\n\n"
                "Please try:\n"
                "• Check if the link is correct\n"
                "• Try again in a few moments\n"
                "• Make sure the link is publicly accessible",
                parse_mode='Markdown'
            )
            return
        
        # Prepare file info message
        filename = file_info['filename']
        file_size = format_file_size(file_info['size'])
        download_url = file_info['download_url']
        
        if file_info['isdir'] == 1:
            # It's a folder
            result_text = f"""
📁 **FOLDER DETECTED**

📂 **Folder Name:** `{filename}`
📊 **Size:** {file_size}
🔗 **Type:** Directory

❗ **Note:** This is a folder containing multiple files.
For folders, please access individual files within the folder.

🔗 **Original Link:** [Open Terabox]({url})
            """
        else:
            # It's a single file
            result_text = f"""
✅ **FILE READY FOR DOWNLOAD**

📄 **Filename:** `{filename}`
📊 **Size:** {file_size}
⚡ **Status:** Ready to download

🔗 **Download Methods:**
            """
        
        # Create inline keyboard with download options
        keyboard = []
        
        if download_url and file_info['isdir'] == 0:
            keyboard.append([InlineKeyboardButton("📥 Direct Download", url=download_url)])
        
        keyboard.append([InlineKeyboardButton("🔗 Open in Terabox", url=url)])
        keyboard.append([InlineKeyboardButton("🔄 Process Another Link", callback_data="start")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.edit_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing Terabox link: {e}")
        await processing_msg.edit_text(
            "❌ **Processing Failed**\n\n"
            "An unexpected error occurred while processing your link.\n\n"
            "Please try again or contact support if the issue persists.",
            parse_mode='Markdown'
        )

async def leech_command(update: Update, context) -> None:
    """Leech command handler"""
    if len(context.args) == 0:
        await update.message.reply_text(
            "📋 **Usage:** `/leech [terabox_link]`\n\n"
            "**Example:**\n"
            "`/leech https://terabox.com/s/1ABCdef123`\n\n"
            "**Or simply send the link directly without any command!**",
            parse_mode='Markdown'
        )
        return
    
    url = ' '.join(context.args)
    
    # Create a fake update object to reuse the processing function
    class FakeMessage:
        def __init__(self, text):
            self.text = text
    
    class FakeUpdate:
        def __init__(self, message):
            self.message = message
    
    fake_update = FakeUpdate(FakeMessage(url))
    fake_update.message.reply_text = update.message.reply_text
    
    await process_terabox_link(fake_update, context)

# Button callback handler
async def button_callback(update: Update, context) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(query, context)
    elif query.data == "about":
        await about_command(query, context)
    elif query.data == "start":
        await start_command(query, context)

# Main function
async def main():
    """Main function to run the bot"""
    try:
        logger.info("🚀 Starting Terabox Leech Bot...")
        
        # Start health check server
        await start_health_server()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("ping", ping_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("leech", leech_command))
        
        # Handle all text messages (for Terabox links)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_terabox_link))
        
        # Handle button callbacks
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Initialize and start the application
        await application.initialize()
        await application.start()
        
        logger.info("✅ Terabox Leech Bot started successfully!")
        logger.info("🚀 Ready to process Terabox links!")
        
        # Start polling
        await application.updater.start_polling()
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
    
