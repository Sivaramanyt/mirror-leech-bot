import logging
from pyrogram import filters
from pyrogram.types import Message

logger = logging.getLogger(__name__)

def setup_message_handlers(app):
    """Setup message handlers - simplified"""
    
    @app.on_message(filters.text & filters.private)
    async def handle_all_messages(client, message: Message):
        # Skip if it's a command
        if message.text.startswith('/'):
            return
            
        text = message.text.strip()
        user_id = message.from_user.id
        
        # Simple URL check
        if text.startswith('http'):
            await message.reply_text(
                f"🔗 **URL Received!**\n\n"
                f"✅ Bot is working correctly!\n"
                f"Use `/leech {text[:30]}...` to process this URL"
            )
        else:
            await message.reply_text(
                "👋 **Hello!**\n\n"
                "Send me a URL or use `/help` for commands!"
            )
        
        logger.info(f"Message from user {user_id}")
        
