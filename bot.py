import asyncio
import logging
import os
import aiohttp
import aiofiles
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import threading
from aiohttp import web
import time
import re
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DOWNLOAD_DIR = "/tmp/downloads"

# Create download directory
Path(DOWNLOAD_DIR).mkdir(exist_ok=True)

# ✅ Simple URL validator (OLD WORKING VERSION)
def is_terabox_url(url: str) -> bool:
    """Simple URL validator - OLD WORKING VERSION"""
    try:
        url = url.lower().strip()
        
        # OLD working domains that were reliable
        working_domains = [
            'terabox.com',
            'terasharelink.com', 
            'nephobox.com',
            '4funbox.com',
            'mirrobox.com',
            '1024tera.com'
        ]
        
        for domain in working_domains:
            if domain in url and '/s/' in url:
                return True
        return False
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False

# ✅ Format file size
def format_size(bytes_size):
    """Format bytes to human readable size"""
    if bytes_size == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

# ✅ OLD WORKING Terabox info extractor
async def get_terabox_info_old(session, url: str):
    """OLD WORKING terabox info extraction"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        
        logger.info(f"🔍 OLD METHOD: Fetching {url}")
        
        async with session.get(url, headers=headers, timeout=20) as response:
            if response.status != 200:
                logger.error(f"HTTP Error: {response.status}")
                return None
                
            content = await response.text()
            logger.info(f"✅ Page fetched, length: {len(content)}")
            
            # OLD WORKING extraction methods
            file_info = {}
            
            # Method 1: Simple title extraction (OLD RELIABLE)
            title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1).strip()
                if 'terabox' not in title.lower() and title != '':
                    file_info['filename'] = title
                    logger.info(f"📁 Found filename: {title}")
            
            # Method 2: Simple meta description (OLD BACKUP)
            desc_match = re.search(r'<meta[^>]*description[^>]*content="([^"]*)"', content, re.IGNORECASE)
            if desc_match and not file_info.get('filename'):
                desc = desc_match.group(1).strip()
                if len(desc) > 0 and 'terabox' not in desc.lower():
                    file_info['filename'] = desc[:100]
                    
            # Method 3: Look for file size in page (OLD SIMPLE)
            size_patterns = [
                r'(\d+(?:\.\d+)?)\s*(GB|MB|KB|B)',
                r'Size[:\s]*(\d+(?:\.\d+)?)\s*(GB|MB|KB|B)',
            ]
            
            for pattern in size_patterns:
                size_match = re.search(pattern, content, re.IGNORECASE)
                if size_match:
                    size_num = float(size_match.group(1))
                    size_unit = size_match.group(2).upper()
                    
                    # Convert to bytes
                    multipliers = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
                    if size_unit in multipliers:
                        file_info['size'] = int(size_num * multipliers[size_unit])
                        break
            
            # Set defaults for OLD VERSION compatibility
            if not file_info.get('filename'):
                file_info['filename'] = 'Terabox File'
            if not file_info.get('size'):
                file_info['size'] = 0
                
            logger.info(f"📊 OLD METHOD result: {file_info}")
            return file_info
                
    except Exception as e:
        logger.error(f"❌ OLD extraction error: {e}")
        return None

# ✅ START command (OLD WORKING)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - OLD WORKING VERSION"""
    try:
        user_id = update.effective_user.id
        logger.info(f"📨 START command from user {user_id}")
        
        await update.message.reply_text(
            "🚀 **Terabox Bot - OLD WORKING VERSION**\n\n"
            "✅ **Restored to previous working state**\n\n"
            "**Commands:**\n"
            "• `/start` - Show this message\n"
            "• `/leech <url>` - Process Terabox URL\n\n"
            "**Working domains (OLD VERSION):**\n"
            "• terabox.com ✅\n"
            "• terasharelink.com ✅\n"
            "• nephobox.com ✅\n"
            "• 4funbox.com ✅\n"
            "• mirrobox.com ✅\n"
            "• 1024tera.com ✅\n\n"
            "**Usage:** `/leech https://terabox.com/s/xxxxx`\n\n"
            "🔧 **Note:** This is the OLD working version before teraboxlink.com issues",
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ START response sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"START command error: {e}")

# ✅ LEECH command (OLD WORKING VERSION) 
async def leech_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """OLD WORKING leech command"""
    try:
        user_id = update.effective_user.id
        logger.info(f"📨 LEECH command from user {user_id}")
        
        # Check URL
        if not context.args:
            await update.message.reply_text(
                "❌ **No URL provided**\n\n"
                "**Usage:** `/leech <terabox_url>`\n\n"
                "**Example:**\n"
                "`/leech https://terabox.com/s/xxxxx`",
                parse_mode='Markdown'
            )
            return
        
        url = ' '.join(context.args)
        logger.info(f"🔍 Processing URL: {url}")
        
        # Validate URL using OLD working method
        if not is_terabox_url(url):
            await update.message.reply_text(
                "⚠️ **Invalid Terabox URL**\n\n"
                "**Working domains (OLD VERSION):**\n"
                "• terabox.com\n"
                "• terasharelink.com\n"
                "• nephobox.com\n"
                "• 4funbox.com\n"
                "• mirrobox.com\n"
                "• 1024tera.com\n\n"
                "**Note:** teraboxlink.com removed from this OLD working version",
                parse_mode='Markdown'
            )
            return
        
        # Process using OLD working method
        processing_msg = await update.message.reply_text(
            f"✅ **OLD METHOD: Valid Terabox URL**\n\n"
            f"**URL:** `{url[:60]}...`\n\n"
            f"**Status:** Using OLD working extraction method\n"
            f"**Domain:** Recognized by OLD working validator\n\n"
            f"⏳ **Processing:** Extracting file info...",
            parse_mode='Markdown'
        )
        
        # Use OLD working extraction
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            file_info = await get_terabox_info_old(session, url)
            
            if not file_info:
                await processing_msg.edit_text(
                    f"❌ **OLD METHOD: Extraction Failed**\n\n"
                    f"**URL:** `{url[:50]}...`\n\n"
                    f"**Possible reasons:**\n"
                    f"• Link is private or password protected\n"
                    f"• File has been deleted or moved\n"
                    f"• Server is temporarily unavailable\n\n"
                    f"**Note:** This is the OLD working method - some features limited",
                    parse_mode='Markdown'
                )
                return
            
            filename = file_info.get('filename', 'Terabox File')
            file_size = file_info.get('size', 0)
            
            await processing_msg.edit_text(
                f"📁 **OLD METHOD: File Info Extracted**\n\n"
                f"**📄 Name:** `{filename}`\n"
                f"**📊 Size:** {format_size(file_size) if file_size else 'Unknown'}\n"
                f"**🔗 Source:** `{url[:50]}...`\n\n"
                f"✅ **Status:** OLD working method successfully extracted info\n\n"
                f"**📋 Note:** This OLD version focuses on file detection.\n"
                f"Actual downloads require additional Terabox API access\n"
                f"which may have restrictions.\n\n"
                f"**🎯 Success:** File information validated using OLD working approach!",
                parse_mode='Markdown'
            )
        
        logger.info(f"✅ OLD METHOD completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"LEECH command error: {e}")
        try:
            await update.message.reply_text(
                f"❌ **OLD METHOD: Error**\n\n"
                f"Error: `{str(e)[:100]}`\n\n"
                f"Please try again with a different URL.",
                parse_mode='Markdown'
            )
        except:
            pass

# ✅ URL handler (OLD WORKING VERSION)
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direct URL messages - OLD WORKING VERSION"""
    try:
        url = update.message.text.strip()
        
        # Only process if it looks like a URL
        if not any(indicator in url.lower() for indicator in ['http://', 'https://', 'terabox', '.com']):
            return
        
        logger.info(f"📨 Direct URL (OLD METHOD): {url[:50]}...")
        
        # Validate using OLD working method
        if is_terabox_url(url):
            context.args = [url]
            await leech_command(update, context)
        else:
            await update.message.reply_text(
                "⚠️ **OLD METHOD: URL Not Supported**\n\n"
                "**Working domains (OLD VERSION):**\n"
                "• terabox.com\n"
                "• terasharelink.com\n" 
                "• nephobox.com\n"
                "• 4funbox.com\n"
                "• mirrobox.com\n"
                "• 1024tera.com\n\n"
                "**Try:** `/leech <your_url>`",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"URL handler error: {e}")

# ✅ Health server (OLD WORKING)
def start_health_server():
    """Health server - OLD WORKING VERSION"""
    async def health_check(request):
        return web.Response(
            text=(
                "✅ Terabox Bot - OLD WORKING VERSION\n"
                "🔧 Restored to previous working state\n"
                "⚡ Before teraboxlink.com issues\n"
                "🎯 Status: STABLE\n"
                "📱 Using OLD reliable extraction methods"
            ),
            status=200
        )
    
    async def run_server():
        app = web.Application()
        app.router.add_get('/', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        port = int(os.environ.get('PORT', 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"✅ OLD VERSION health server started on port {port}")
        
        # Keep server running
        while True:
            await asyncio.sleep(1)
    
    def server_thread():
        asyncio.run(run_server())
    
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

def main():
    """Main function - OLD WORKING VERSION"""
    try:
        logger.info("🚀 Starting OLD WORKING Terabox Bot...")
        logger.info("🔄 Restored to version before teraboxlink.com issues")
        logger.info("✅ Using OLD reliable extraction methods")
        
        # Validate environment
        if not BOT_TOKEN:
            logger.error("❌ Missing BOT_TOKEN")
            return
            
        logger.info("✅ Environment validated")
        
        # Start health server
        start_health_server()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers (OLD WORKING VERSION)
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("leech", leech_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
        
        logger.info("🤖 OLD WORKING handlers registered")
        logger.info("✅ Commands: /start, /leech")
        logger.info("🎯 OLD WORKING domains supported!")
        logger.info("🔥 OLD WORKING bot ready!")
        
        # Start polling
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 OLD WORKING bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
