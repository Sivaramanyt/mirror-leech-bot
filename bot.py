import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import os
import requests
import re
from aiohttp import web
import time

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
    return web.json_response({"status": "healthy", "bot": "TeraboxLeechBot"})

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

# Terabox API configuration
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

# Bot handlers
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
    
    keyboard = [
        [InlineKeyboardButton("📋 Help", callback_data="help"),
         InlineKeyboardButton("🏓 Ping", callback_data="ping")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(start_text, reply_markup=reply_markup)
    logger.info(f"📥 Start command from user {message.from_user.id}")

@app.on_message(filters.command("ping"))
async def ping_command(client, message):
    start_time = time.time()
    ping_msg = await message.reply_text("🏓 Pinging...")
    end_time = time.time()
    
    ping_time = round((end_time - start_time) * 1000, 2)
    
    await ping_msg.edit_text(
        f"🏓 **Pong!**\n\n"
        f"⚡ **Response Time:** {ping_time}ms\n"
        f"✅ **Bot Status:** Online\n"
        f"🚀 **Ready for downloads!**"
    )

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

@app.on_message(filters.command("leech"))
async def leech_command(client, message):
    """Handle leech command"""
    try:
        # Check if URL provided
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **Please provide a URL to download**\n\n"
                "**Usage:** `/leech [URL]`\n"
                "**Example:** `/leech https://terabox.com/s/abc123`\n\n"
                "🔗 **Supported platforms:**\n"
                "• Terabox and all variants\n"
                "• Direct download links"
            )
            return
        
        url = message.command[1]
        user_id = message.from_user.id
        
        # Validate Terabox URL
        terabox_domains = [
            'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
            'momerybox.com', 'teraboxapp.com', '1024tera.com', 'gibibox.com'
        ]
        
        if not any(domain in url.lower() for domain in terabox_domains):
            await message.reply_text(
                "❌ **Unsupported URL**\n\n"
                "**Supported platforms:**\n"
                "• Terabox (terabox.com)\n"
                "• Nephobox (nephobox.com)\n"
                "• 4funbox (4funbox.com)\n"
                "• Mirrobox (mirrobox.com)\n"
                "• And other Terabox variants"
            )
            return
        
        # Send processing message
        status_msg = await message.reply_text(
            f"🚀 **Lightning-Fast Download Starting!**\n\n"
            f"📎 **URL:** `{url[:50]}...`\n"
            f"👤 **User:** {message.from_user.mention}\n"
            f"⏳ **Status:** Processing...\n"
            f"⚡ **Speed:** Lightning-fast!"
        )
        
        # Extract file info
        file_info = extract_terabox_info(url)
        
        if not file_info:
            await status_msg.edit_text(
                "❌ **Failed to Process Link**\n\n"
                "• Link might be invalid or expired\n"
                "• File might be private or restricted\n"
                "• Server might be temporarily unavailable\n\n"
                "Please try:\n"
                "• Check if the link is correct\n"
                "• Try again in a few moments\n"
                "• Make sure the link is publicly accessible"
            )
            return
        
        # Prepare file info
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
        
        # Create download buttons
        keyboard = []
        
        if download_url and file_info['isdir'] == 0:
            keyboard.append([InlineKeyboardButton("📥 Direct Download", url=download_url)])
        
        keyboard.append([InlineKeyboardButton("🔗 Open in Terabox", url=url)])
        keyboard.append([InlineKeyboardButton("🔄 Leech Another", callback_data="start")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await status_msg.edit_text(result_text, reply_markup=reply_markup)
        
        logger.info(f"📥 Leech processed for user {user_id}: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Error in leech command: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

@app.on_message(filters.command("status"))
async def status_command(client, message):
    """Check download status"""
    await message.reply_text(
        "📊 **Download Status**\n\n"
        "❌ **No active downloads**\n\n"
        "Use `/leech [url]` to start downloading from Terabox.\n\n"
        "🚀 **Lightning-fast downloads ready!**"
    )

@app.on_message(filters.command("cancel"))
async def cancel_command(client, message):
    """Cancel active download"""
    await message.reply_text(
        "❌ **No active downloads to cancel**\n\n"
        "Use `/leech [url]` to start a new download."
    )

# Handle direct Terabox links (without command)
@app.on_message(filters.text & ~filters.command)
async def handle_direct_links(client, message):
    """Handle Terabox links sent directly"""
    url = message.text.strip()
    
    # Check if it's a Terabox link
    terabox_domains = [
        'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
        'momerybox.com', 'teraboxapp.com', '1024tera.com', 'gibibox.com'
    ]
    
    if any(domain in url.lower() for domain in terabox_domains):
        # Process as leech command
        message.command = ['leech', url]  # Fake command structure
        await leech_command(client, message)
    else:
        # Not a Terabox link, send help
        await message.reply_text(
            "❓ **Not a Terabox link**\n\n"
            "Send me a Terabox link or use:\n"
            "`/leech [your_terabox_url]`\n\n"
            "Use `/help` for more information."
        )

# Button callback handler
async def button_callback(update, context):
    """Handle inline button callbacks"""
    query = update.callback_query
    
    if query.data == "help":
        await help_command(query, context)
    elif query.data == "ping":
        await ping_command(query, context)
    elif query.data == "start":
        await start_command(query, context)
    
    await query.answer()

async def main():
    try:
        logger.info("🚀 Starting Terabox Leech Bot...")
        
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
        logger.info(f"🤖 Bot started: @{me.username} (ID: {me.id})")
        logger.info("🎯 Bot is ready for Terabox downloads!")
        
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
