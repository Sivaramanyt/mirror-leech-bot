import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from pyrogram import Client
from pyrogram.types import Message
import aiofiles
from .helpers import get_readable_file_size
from .database import db
import time
import math

logger = logging.getLogger(__name__)

class MirrorEngine:
    def __init__(self):
        self.active_uploads = {}
        self.chunk_size = 1024 * 1024 * 10  # 10MB chunks
        
    async def mirror_to_telegram(self, client: Client, message: Message, file_path: str, 
                                caption: str = None, progress_callback: Optional = None) -> Dict[str, Any]:
        """Mirror file to Telegram with splitting if needed"""
        try:
            user_id = message.from_user.id
            
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'File not found',
                    'files': []
                }
            
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            # Check if file needs splitting (Telegram limit: 2GB)
            max_size = 2 * 1024 * 1024 * 1024  # 2GB
            
            if file_size <= max_size:
                # Upload as single file
                result = await self._upload_single_file(client, message, file_path, caption, progress_callback)
            else:
                # Split and upload multiple files
                result = await self._upload_split_files(client, message, file_path, caption, progress_callback)
            
            if result['success']:
                # Log to database
                if db.enabled:
                    await db.log_download(user_id, filename, file_size, "mirror_upload")
                
                logger.info(f"✅ Mirror completed for user {user_id}: {filename}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Mirror error: {e}")
            return {
                'success': False,
                'error': str(e),
                'files': []
            }
    
    async def _upload_single_file(self, client: Client, message: Message, file_path: str, 
                                 caption: str = None, progress_callback: Optional = None) -> Dict[str, Any]:
        """Upload single file to Telegram"""
        try:
            user_id = message.from_user.id
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Track upload
            self.active_uploads[user_id] = {
                'filename': filename,
                'total_size': file_size,
                'uploaded': 0,
                'start_time': time.time(),
                'speed': 0
            }
            
            # Progress callback wrapper
            async def upload_progress(current, total):
                self.active_uploads[user_id]['uploaded'] = current
                elapsed = time.time() - self.active_uploads[user_id]['start_time']
                if elapsed > 0:
                    speed = current / elapsed
                    self.active_uploads[user_id]['speed'] = speed
                
                if progress_callback:
                    await progress_callback(current, total, speed)
            
            # Upload file
            sent_message = await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption=caption or f"📁 **{filename}**\n📊 **Size:** {get_readable_file_size(file_size)}",
                progress=upload_progress
            )
            
            # Remove from active uploads
            if user_id in self.active_uploads:
                del self.active_uploads[user_id]
            
            return {
                'success': True,
                'files': [sent_message],
                'total_size': file_size,
                'upload_time': time.time() - self.active_uploads.get(user_id, {}).get('start_time', time.time())
            }
            
        except Exception as e:
            # Remove from active uploads on error
            if user_id in self.active_uploads:
                del self.active_uploads[user_id]
            
            logger.error(f"❌ Upload error: {e}")
            return {
                'success': False,
                'error': str(e),
                'files': []
            }
    
    async def _upload_split_files(self, client: Client, message: Message, file_path: str, 
                                 caption: str = None, progress_callback: Optional = None) -> Dict[str, Any]:
        """Upload file in multiple parts"""
        try:
            user_id = message.from_user.id
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Calculate number of parts
            max_part_size = 2 * 1024 * 1024 * 1024 - 1024 * 1024  # 2GB - 1MB buffer
            num_parts = math.ceil(file_size / max_part_size)
            
            uploaded_files = []
            
            # Track upload
            self.active_uploads[user_id] = {
                'filename': filename,
                'total_size': file_size,
                'uploaded': 0,
                'start_time': time.time(),
                'speed': 0,
                'current_part': 0,
                'total_parts': num_parts
            }
            
            async with aiofiles.open(file_path, 'rb') as source_file:
                for part_num in range(num_parts):
                    part_filename = f"{filename}.part{part_num + 1:03d}"
                    part_path = f"{file_path}.part{part_num + 1:03d}"
                    
                    # Create part file
                    async with aiofiles.open(part_path, 'wb') as part_file:
                        bytes_to_read = min(max_part_size, file_size - (part_num * max_part_size))
                        
                        while bytes_to_read > 0:
                            chunk_size = min(self.chunk_size, bytes_to_read)
                            chunk = await source_file.read(chunk_size)
                            if not chunk:
                                break
                            
                            await part_file.write(chunk)
                            bytes_to_read -= len(chunk)
                            
                            # Update progress
                            self.active_uploads[user_id]['uploaded'] += len(chunk)
                    
                    # Upload part
                    part_size = os.path.getsize(part_path)
                    part_caption = f"📦 **{filename}**\n🔢 **Part:** {part_num + 1}/{num_parts}\n📊 **Size:** {get_readable_file_size(part_size)}"
                    
                    sent_message = await client.send_document(
                        chat_id=message.chat.id,
                        document=part_path,
                        caption=part_caption
                    )
                    
                    uploaded_files.append(sent_message)
                    
                    # Update current part
                    self.active_uploads[user_id]['current_part'] = part_num + 1
                    
                    # Clean up part file
                    os.remove(part_path)
                    
                    logger.info(f"📤 Uploaded part {part_num + 1}/{num_parts} for {filename}")
            
            # Remove from active uploads
            if user_id in self.active_uploads:
                del self.active_uploads[user_id]
            
            return {
                'success': True,
                'files': uploaded_files,
                'total_size': file_size,
                'parts': num_parts,
                'upload_time': time.time() - self.active_uploads.get(user_id, {}).get('start_time', time.time())
            }
            
        except Exception as e:
            # Remove from active uploads on error
            if user_id in self.active_uploads:
                del self.active_uploads[user_id]
            
            logger.error(f"❌ Split upload error: {e}")
            return {
                'success': False,
                'error': str(e),
                'files': []
            }
    
    async def mirror_to_gdrive(self, file_path: str, folder_id: str = None) -> Dict[str, Any]:
        """Mirror file to Google Drive (placeholder for future implementation)"""
        # TODO: Implement Google Drive upload
        logger.warning("🚧 Google Drive mirror not implemented yet")
        return {
            'success': False,
            'error': 'Google Drive mirror not implemented',
            'gdrive_link': None
        }
    
    def get_active_uploads(self) -> Dict[int, Dict[str, Any]]:
        """Get all active uploads"""
        return self.active_uploads.copy()
    
    def get_user_upload(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get specific user's active upload"""
        return self.active_uploads.get(user_id)
    
    async def cancel_upload(self, user_id: int) -> bool:
        """Cancel user's active upload"""
        if user_id in self.active_uploads:
            del self.active_uploads[user_id]
            logger.info(f"📛 Upload cancelled for user {user_id}")
            return True
        return False

# Global mirror engine instance
mirror_engine = MirrorEngine()
