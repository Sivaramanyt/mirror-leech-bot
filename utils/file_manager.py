import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from utils.database import db
import aiofiles

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self):
        self.default_channel_id = -1003068078005  # Your channel ID
    
    async def get_private_channel_id(self) -> int:
        """Get private channel ID from database settings"""
        try:
            channel_setting = await db.bot_settings_new.find_one({"setting_name": "private_channel_id"})
            
            if not channel_setting:
                # Set default channel ID
                await db.bot_settings_new.insert_one({
                    "setting_name": "private_channel_id",
                    "value": str(self.default_channel_id),
                    "updated_at": datetime.utcnow()
                })
                return self.default_channel_id
            
            return int(channel_setting["value"])
        except Exception as e:
            logger.error(f"❌ Error getting channel ID: {e}")
            return self.default_channel_id
    
    async def forward_to_channel(self, file_path: str, original_filename: str, client) -> Optional[int]:
        """Forward file to private channel anonymously"""
        try:
            channel_id = await self.get_private_channel_id()
            
            # Determine file type
            file_extension = os.path.splitext(original_filename.lower())[1]
            
            if file_extension in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
                # Send as video
                message = await client.send_video(
                    chat_id=channel_id,
                    video=file_path,
                    caption=original_filename,  # Only original filename, no user info
                    supports_streaming=True
                )
            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                # Send as photo
                message = await client.send_photo(
                    chat_id=channel_id,
                    photo=file_path,
                    caption=original_filename
                )
            else:
                # Send as document
                message = await client.send_document(
                    chat_id=channel_id,
                    document=file_path,
                    caption=original_filename
                )
            
            logger.info(f"📤 File forwarded anonymously to channel: {original_filename}")
            return message.id
            
        except Exception as e:
            logger.error(f"❌ Error forwarding file to channel: {e}")
            return None
    
    async def store_file_info(self, original_filename: str, channel_msg_id: int, auto_delete_hours: int = 24):
        """Store file information for tracking and auto-delete"""
        try:
            file_id = f"file_{int(datetime.utcnow().timestamp())}_{channel_msg_id}"
            auto_delete_at = datetime.utcnow() + timedelta(hours=auto_delete_hours)
            
            await db.forwarded_files.insert_one({
                "file_id": file_id,
                "original_filename": original_filename,
                "channel_msg_id": channel_msg_id,
                "user_download_count": 0,
                "created_at": datetime.utcnow(),
                "auto_delete_at": auto_delete_at
            })
            
            logger.info(f"💾 File info stored: {original_filename}, auto-delete at {auto_delete_at}")
            
        except Exception as e:
            logger.error(f"❌ Error storing file info: {e}")
    
    async def schedule_auto_delete(self, file_path: str, original_filename: str, channel_msg_id: int, hours: int = 24):
        """Schedule file for auto-deletion"""
        try:
            await self.store_file_info(original_filename, channel_msg_id, hours)
            
            # Clean up local file immediately after forwarding
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Local file cleaned up: {file_path}")
            
        except Exception as e:
            logger.error(f"❌ Error scheduling auto-delete: {e}")
    
    async def cleanup_expired_files(self, client):
        """Clean up expired files from channel (run periodically)"""
        try:
            current_time = datetime.utcnow()
            expired_files = await db.forwarded_files.find({
                "auto_delete_at": {"$lt": current_time}
            }).to_list(None)
            
            channel_id = await self.get_private_channel_id()
            
            for file_info in expired_files:
                try:
                    # Delete from channel
                    await client.delete_messages(
                        chat_id=channel_id,
                        message_ids=file_info["channel_msg_id"]
                    )
                    
                    # Remove from database
                    await db.forwarded_files.delete_one({"_id": file_info["_id"]})
                    
                    logger.info(f"🗑️ Expired file deleted: {file_info['original_filename']}")
                    
                except Exception as delete_error:
                    logger.error(f"❌ Error deleting expired file: {delete_error}")
                    # Remove from database even if channel deletion failed
                    await db.forwarded_files.delete_one({"_id": file_info["_id"]})
            
            if expired_files:
                logger.info(f"🧹 Cleaned up {len(expired_files)} expired files")
                
        except Exception as e:
            logger.error(f"❌ Error in cleanup process: {e}")

# Initialize file manager
file_manager = FileManager()
