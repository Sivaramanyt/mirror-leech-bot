import asyncio
import os
import logging
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from utils.helpers import get_readable_file_size, get_progress_bar_string
from downloaders.terabox import TeraboxDownloader
from downloaders.direct import DirectDownloader
from downloaders.youtube import YouTubeDownloader
import config

logger = logging.getLogger(__name__)

class LeechHandler:
    def __init__(self, bot):
        self.bot = bot
        self.terabox_downloader = TeraboxDownloader()
        self.direct_downloader = DirectDownloader()
        self.youtube_downloader = YouTubeDownloader()
    
    async def leech_command(self, client, message: Message):
        """Handle /leech command"""
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply_text(
                    "❌ <b>Usage:</b> <code>/leech [URL]</code>\n\n"
                    "<b>Supported links:</b>\n"
                    "• Terabox links\n"
                    "• Direct HTTP/HTTPS links\n"
                    "• YouTube and 900+ sites",
                    parse_mode=ParseMode.HTML
                )
                return
            
            url = args[1].strip()
            task_id = self.bot.generate_task_id()
            
            # Send initial message
            status_msg = await message.reply_text(
                f"🔄 <b>Starting download...</b>\n"
                f"📎 <b>Link:</b> <code>{url[:50]}...</code>",
                parse_mode=ParseMode.HTML
            )
            
            # Add task to active tasks
            self.bot.active_tasks[task_id] = {
                'name': url.split('/')[-1] if '/' in url else 'Unknown',
                'status': 'downloading',
                'message': status_msg,
                'url': url
            }
            
            # Determine downloader
            if 'terabox.com' in url or 'teraboxapp.com' in url or 'nephobox.com' in url:
                downloader = self.terabox_downloader
            elif url.startswith(('http://', 'https://')):
                downloader = self.direct_downloader
            else:
                await status_msg.edit_text("❌ Unsupported link format")
                return
            
            # Download file
            file_path = await downloader.download(
                url, 
                progress_callback=self.download_progress_callback,
                task_id=task_id
            )
            
            if file_path and os.path.exists(file_path):
                # Update status to uploading
                await status_msg.edit_text(
                    f"📤 <b>Uploading to Telegram...</b>\n"
                    f"📄 <b>File:</b> {os.path.basename(file_path)}",
                    parse_mode=ParseMode.HTML
                )
                
                # Upload to Telegram with video detection
                await self.upload_to_telegram(file_path, message, task_id)
                
                # Clean up
                try:
                    os.remove(file_path)
                except:
                    pass
                
                await status_msg.delete()
                
            else:
                await status_msg.edit_text("❌ <b>Download failed!</b>", parse_mode=ParseMode.HTML)
        
        except Exception as e:
            logger.error(f"Leech error: {e}")
            await message.reply_text(f"❌ <b>Error:</b> {str(e)}", parse_mode=ParseMode.HTML)
        finally:
            # Remove from active tasks
            if task_id in self.bot.active_tasks:
                del self.bot.active_tasks[task_id]
    
    async def upload_to_telegram(self, file_path: str, message: Message, task_id: str):
        """Upload file to Telegram with proper video/document detection"""
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # File extension categories
            video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
            audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg'}
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Check file size limit
            if file_size > config.MAX_FILE_SIZE:
                await message.reply_text(f"❌ File too large: {get_readable_file_size(file_size)}")
                return
            
            # Determine file type and upload accordingly
            if file_ext in video_extensions:
                # Send as video
                await message.reply_video(
                    video=file_path,
                    caption=f"🎥 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
                await message.reply_text("✅ **Leech completed successfully!**", parse_mode=ParseMode.HTML)
                
            elif file_ext in audio_extensions:
                # Send as audio
                await message.reply_audio(
                    audio=file_path,
                    caption=f"🎵 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                    parse_mode=ParseMode.HTML
                )
                await message.reply_text("✅ **Leech completed successfully!**", parse_mode=ParseMode.HTML)
                
            elif file_ext in image_extensions:
                # Send as photo
                await message.reply_photo(
                    photo=file_path,
                    caption=f"🖼️ <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                    parse_mode=ParseMode.HTML
                )
                await message.reply_text("✅ **Leech completed successfully!**", parse_mode=ParseMode.HTML)
                
            else:
                # Send as document
                await message.reply_document(
                    document=file_path,
                    caption=f"📄 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                    parse_mode=ParseMode.HTML
                )
                await message.reply_text("✅ **Leech completed successfully!**", parse_mode=ParseMode.HTML)
                
        except Exception as e:
            logger.error(f"Upload error: {e}")
            await message.reply_text(f"❌ Upload failed: {str(e)}")
    
    async def download_progress_callback(self, downloaded: int, total: int, task_id: str):
        """Progress callback for downloads"""
        if task_id in self.bot.active_tasks:
            task_info = self.bot.active_tasks[task_id]
            percentage = (downloaded / total) * 100 if total > 0 else 0
            
            progress_bar = get_progress_bar_string(percentage)
            status_text = (
                f"📥 <b>Downloading...</b>\n"
                f"📄 <b>File:</b> {task_info.get('name', 'Unknown')}\n"
                f"📊 <b>Progress:</b> {percentage:.1f}%\n"
                f"📦 <b>Size:</b> {get_readable_file_size(downloaded)} / {get_readable_file_size(total)}\n"
                f"{progress_bar}"
            )
            
            try:
                await task_info['message'].edit_text(status_text, parse_mode=ParseMode.HTML)
            except:
                pass
            
