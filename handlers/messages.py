import asyncio
import logging
from urllib.parse import urlparse
from pyrogram import filters
from pyrogram.types import Message

logger = logging.getLogger(__name__)

# Terabox domains list
TERABOX_DOMAINS = [
    'terabox.com',
    'terasharelink.com',
    'nephobox.com',
    '4funbox.com', 
    'mirrobox.com',
    '1024tera.com',
    '1024terabox.com',
    'momerybox.com',
    'tibibox.com',
    'teraboxapp.com'
]

def is_terabox_url(url: str) -> bool:
    """Check if URL is from supported Terabox domains"""
    try:
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc.replace('www.', '')
        
        for terabox_domain in TERABOX_DOMAINS:
            if terabox_domain in domain and '/s/' in url:
                return True
        return False
    except:
        return False

async def handle_message(client, message: Message):
    """Handle incoming messages"""
    try:
        if not message.text:
            return
            
        text = message.text.strip()
        
        # Check if message contains a Terabox URL
        if is_terabox_url(text):
            logger.info(f"📨 Terabox URL detected from user {message.from_user.id}")
            
            await message.reply_text(
                f"✅ **Terabox URL Detected!**\n\n"
                f"🔗 **URL:** `{text[:50]}...`\n\n"
                f"⏳ **Processing:** Starting Terabox download...\n\n"
                f"🎯 **Status:** Your file will be processed and uploaded to Telegram."
            )
            
            # Here you would call your Terabox download function
            # await process_terabox_download(client, message, text)
            
        else:
            # Handle other types of messages
            await message.reply_text(
                "ℹ️ **Send a Terabox link to download files**\n\n"
                "**Supported domains:**\n"
                "• terabox.com\n"
                "• terasharelink.com\n"
                "• nephobox.com\n"
                "• 4funbox.com\n"
                "• mirrobox.com\n"
                "• 1024terabox.com"
            )
            
    except Exception as e:
        logger.error(f"Message handler error: {e}")

def setup_message_handlers(app):
    """Setup message handlers"""
    try:
        @app.on_message(filters.text & filters.private)
        async def message_handler(client, message):
            await handle_message(client, message)
            
        logger.info("✅ Message handlers setup complete")
    except Exception as e:
        logger.error(f"❌ Message handlers setup failed: {e}")
        
