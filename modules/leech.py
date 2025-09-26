import asyncio
import os
import logging
from pyrogram import Client
from pyrogram.types import Message
from utils.helpers import *
from downloaders.terabox import TeraboxDownloader
from downloaders.youtube import YouTubeDownloader
from downloaders.direct import DirectDownloader

logger = logging.getLogger(__name__)

class LeechHandler:
    def __init__(self, bot):
        self.bot = bot
        
    async def leech_command(self, client: Client, message: Message):
        """Handle /leech command"""
        args = message.text.split()
        
        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:** `/leech [link]`\n\n"
                "**Examples:**\n"
                "• `/leech https://terabox.com/s/xxxxx`\n"
                "• `/leech https://example.com/file.zip`\n"
                "• `/leech https://mega.nz/file/xxxxx`"
            )
            return
            
        url = args[1]
        task_id = self.bot.generate_task_id()
        
        # Determine downloader type
        if is_terabox_link(url):
            downloader = TeraboxDownloader()
        elif is_youtube_link(url):
            downloader = YouTubeDownloader()
        else:
            downloader = DirectDownloader()
            
        # Get filename
        filename = extract_filename_from_url(url)
        
        # Add to active tasks
        self.bot.active_tasks[task_id] = {
            'name': filename,
            'status': 'downloading',
            'progress': 0,
            'user_id': message.from_user.id
        }
        
        status_msg = await message.reply_text(f"📥 **Downloading...**\n📁 {filename[:50]}...")
        
        try:
            # Download file
            file_path = await downloader.download(url, self.progress_callback, task_id)
            
            if not file_path or not os.path.exists(file_path):
                await status_msg.edit_text("❌ **Download failed!**")
                return
                
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > config.MAX_FILE_SIZE:
                await status_msg.edit_text("❌ **File too large for free tier!**")
                return
                
            await status_msg.edit_text("📤 **Uploading to Telegram...**")
            
            # Upload to Telegram
            upload_chat = config.LEECH_DUMP_CHAT or message.chat.id
            
            if file_size > 50 * 1024 * 1024:  # 50MB+ split into parts
                await self.upload_large_file(client, file_path, upload_chat, status_msg)
            else:
                await client.send_document(
                    chat_id=upload_chat,
                    document=file_path,
                    caption=f"📁 **{os.path.basename(file_path)}**\n🔗 {url}",
                    progress=self.upload_progress,
                    progress_args=(status_msg, os.path.basename(file_path))
                )
                
            await status_msg.edit_text("✅ **Leech completed successfully!**")
            
            # Clean up downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)
                
        except Exception as e:
            logger.error(f"Leech error: {e}")
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")
        finally:
            self.bot.active_tasks.pop(task_id, None)
            
    async def upload_large_file(self, client: Client, file_path: str, chat_id: int, status_msg):
        """Upload large files in parts"""
        file_size = os.path.getsize(file_path)
        part_size = config.LEECH_SPLIT_SIZE
        parts = split_file_size(file_size, part_size)
        
        filename = os.path.basename(file_path)
        base_name = os.path.splitext(filename)[0]
        extension = os.path.splitext(filename)[1]
        
        with open(file_path, 'rb') as f:
            for i, size in enumerate(parts, 1):
                part_name = f"{base_name}.part{i:03d}{extension}"
                part_path = f"/tmp/{part_name}"
                
                # Create part file
                with open(part_path, 'wb') as part_file:
                    part_file.write(f.read(size))
                
                await status_msg.edit_text(f"📤 **Uploading part {i}/{len(parts)}...**")
                
                # Upload part
                await client.send_document(
                    chat_id=chat_id,
                    document=part_path,
                    caption=f"📁 **{part_name}** (Part {i}/{len(parts)})"
                )
                
                # Clean up part file
                os.remove(part_path)
                
    async def progress_callback(self, current: int, total: int, task_id: str):
        """Download progress callback"""
        if task_id in self.bot.active_tasks:
            progress = (current / total) * 100 if total > 0 else 0
            self.bot.active_tasks[task_id]['progress'] = progress
            
    async def upload_progress(self, current: int, total: int, status_msg, filename: str):
        """Upload progress callback"""
        try:
            progress = (current / total) * 100 if total > 0 else 0
            if progress % 10 == 0:  # Update every 10%
                await status_msg.edit_text(
                    f"📤 **Uploading:** {filename[:30]}...\n"
                    f"📊 **Progress:** {progress:.1f}%"
                )
        except:
            pass
