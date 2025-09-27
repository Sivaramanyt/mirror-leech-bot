import logging
import os
from pyrogram import Client
from pyrogram.types import Message
from datetime import datetime

logger = logging.getLogger(__name__)

class Forwarder:
    def __init__(self):
        self.PRIVATE_CHANNEL_ID = os.environ.get("PRIVATE_CHANNEL_ID", "")
        self.enabled = True

    async def forward_file(self, client: Client, message: Message, filename: str, user_id: int) -> bool:
        """Forward file to private channel"""
        if not self.enabled or not self.PRIVATE_CHANNEL_ID:
            return False
        
        try:
            caption = f"""
🔥 **ANONYMOUS DOWNLOAD**

📁 **File:** {filename}
👤 **User ID:** {user_id}
⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔗 **Source:** Terabox
⚡ **Bot:** @Terabox_leech_pro_bot
            """.strip()
            
            await client.copy_message(
                chat_id=self.PRIVATE_CHANNEL_ID,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=caption
            )
            
            logger.info(f"📤 Forwarded: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Forward error: {e}")
            return False

# Global instance
forwarder = Forwarder()
