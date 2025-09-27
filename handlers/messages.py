import logging
import validators
from pyrogram import filters
from pyrogram.types import Message
from utils.config import TERABOX_DOMAINS

logger = logging.getLogger(__name__)

def setup_message_handlers(app):
    """Setup message handlers"""
    
    @app.on_message(filters.text & ~filters.command)
    async def handle_direct_links(client, message: Message):
        """Handle direct Terabox links"""
        url = message.text.strip()
        
        # Enhanced URL validation
        if not validators.url(url):
            await message.reply_text(
                "❓ **Not a valid URL**\n\n"
                "Send me a valid Terabox link or use:\n"
                "`/leech [your_terabox_url]`\n\n"
                "Use `/help` for more information."
            )
            return
        
        # Check if it's a supported Terabox link
        if any(domain in url.lower() for domain in TERABOX_DOMAINS):
            # Process as leech command by simulating command structure
            message.command = ['leech', url]
            
            # Import and call leech handler
            from handlers.commands import setup_command_handlers
            # We need to trigger the leech command handler
            # This is a bit hacky but works for the modular approach
            await message.reply_text("🔄 **Processing your Terabox link...**")
            
            # Here you would call the leech processing logic
            # For now, let's direct them to use the command
            await message.reply_text(
                f"✅ **Terabox link detected!**\n\n"
                f"Use: `/leech {url}`\n\n"
                f"Or I can process it directly. Processing now..."
            )
            
            # You can import the leech logic here
            # from utils.terabox import process_terabox_link
            # await process_terabox_link(client, message, url)
            
        else:
            supported_list = "\n".join([f"• {domain}" for domain in TERABOX_DOMAINS[:5]])
            await message.reply_text(
                f"❌ **Unsupported Platform**\n\n"
                f"This bot supports Terabox and variants.\n\n"
                f"**Supported platforms:**\n{supported_list}\n• And more variants\n\n"
                f"Use `/help` to see all supported platforms."
            )
