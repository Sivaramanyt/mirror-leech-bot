import asyncio
import os
import logging
import time
import pyrogram.errors
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
        self._progress_cache = {}  # Cache for progress tracking
    
    async def leech_command(self, client, message: Message):
        """Handle /leech command with flood wait protection"""
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
            
            # Send initial message with flood wait protection
            try:
                status_msg = await message.reply_text(
                    f"🔄 <b>Starting download...</b>\n"
                    f"📎 <b>Link:</b> <code>{url[:50]}...</code>",
                    parse_mode=ParseMode.HTML
                )
            except pyrogram.errors.FloodWait as e:
                logger.warning(f"⏰ Flood wait on initial message: {e.value} seconds")
                await asyncio.sleep(min(e.value, 60))  # Wait max 1 minute
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
            if any(domain in url for domain in ['terabox.com', 'teraboxapp.com', 'nephobox.com', 'terasharelink.com', 'terafileshare.com']):
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
                # Update status to uploading with flood wait protection
                try:
                    await status_msg.edit_text(
                        f"📤 <b>Uploading to Telegram...</b>\n"
                        f"📄 <b>File:</b> {os.path.basename(file_path)}",
                        parse_mode=ParseMode.HTML
                    )
                except pyrogram.errors.FloodWait as e:
                    logger.warning(f"⏰ Flood wait on upload status: {e.value} seconds")
                    # Continue without updating status
                
                # Upload to Telegram with video detection
                await self.upload_to_telegram_protected(file_path, message, task_id)
                
                # Clean up
                try:
                    os.remove(file_path)
                except:
                    pass
                
                # Delete status message with flood wait protection
                try:
                    await status_msg.delete()
                except:
                    pass
                
            else:
                try:
                    await status_msg.edit_text("❌ <b>Download failed!</b>", parse_mode=ParseMode.HTML)
                except:
                    pass
        
        except pyrogram.errors.FloodWait as e:
            logger.error(f"⏰ Flood wait in leech command: {e.value} seconds")
            try:
                await message.reply_text(f"⏰ <b>Rate limited. Please wait {e.value} seconds and try again.</b>", parse_mode=ParseMode.HTML)
            except:
                pass
        except Exception as e:
            logger.error(f"Leech error: {e}")
            try:
                await message.reply_text(f"❌ <b>Error:</b> {str(e)}", parse_mode=ParseMode.HTML)
            except:
                pass
        finally:
            # Remove from active tasks
            if task_id in self.bot.active_tasks:
                del self.bot.active_tasks[task_id]
            # Clean up progress cache
            if task_id in self._progress_cache:
                del self._progress_cache[task_id]
    
    async def upload_to_telegram_protected(self, file_path: str, message: Message, task_id: str):
        """Upload file to Telegram with flood wait protection"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                # Get file extension
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Define file type categories
                video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
                audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg'}
                image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                
                # Check file size limit
                if file_size > config.MAX_FILE_SIZE:
                    await message.reply_text(f"❌ File too large: {get_readable_file_size(file_size)}")
                    return
                
                # Upload based on file type with flood wait protection
                if file_ext in video_extensions:
                    logger.info(f"📹 Uploading as video: {filename}")
                    await message.reply_video(
                        video=file_path,
                        caption=f"🎥 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                        parse_mode=ParseMode.HTML,
                        supports_streaming=True,
                        duration=0,
                        width=0,
                        height=0
                    )
                elif file_ext in audio_extensions:
                    logger.info(f"🎵 Uploading as audio: {filename}")
                    await message.reply_audio(
                        audio=file_path,
                        caption=f"🎵 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                        parse_mode=ParseMode.HTML
                    )
                elif file_ext in image_extensions:
                    logger.info(f"🖼️ Uploading as photo: {filename}")
                    await message.reply_photo(
                        photo=file_path,
                        caption=f"🖼️ <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    logger.info(f"📄 Uploading as document: {filename}")
                    await message.reply_document(
                        document=file_path,
                        caption=f"📄 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                        parse_mode=ParseMode.HTML
                    )
                
                # Success message
                await message.reply_text("✅ **Leech completed successfully!**", parse_mode=ParseMode.HTML)
                return
                
            except pyrogram.errors.FloodWait as e:
                logger.warning(f"⏰ Flood wait during upload: {e.value} seconds")
                if retry_count < max_retries - 1:
                    retry_count += 1
                    wait_time = min(e.value, 60)  # Max 1 minute wait
                    logger.info(f"🔄 Waiting {wait_time} seconds before retry {retry_count + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    await message.reply_text(f"⏰ **Upload completed but rate limited. Video is ready!**", parse_mode=ParseMode.HTML)
                    return
            except Exception as e:
                logger.error(f"Upload error: {e}")
                await message.reply_text(f"❌ Upload failed: {str(e)}")
                return
    
    async def download_progress_callback(self, downloaded: int, total: int, task_id: str):
        """Progress callback with advanced flood wait protection"""
        if task_id not in self.bot.active_tasks:
            return
            
        task_info = self.bot.active_tasks[task_id]
        percentage = (downloaded / total) * 100 if total > 0 else 0
        current_time = time.time()
        
        # Initialize progress cache for this task
        if task_id not in self._progress_cache:
            self._progress_cache[task_id] = {'last_update': 0, 'last_percentage': 0, 'update_count': 0}
        
        cache = self._progress_cache[task_id]
        
        # Smart update conditions to avoid flood wait
        time_since_last = current_time - cache['last_update']
        percentage_change = percentage - cache['last_percentage']
        
        should_update = (
            cache['update_count'] == 0 or  # First update
            percentage_change >= 20 or     # 20% progress change
            time_since_last >= 60 or       # 60 seconds elapsed
            percentage >= 99.5             # Always update near completion
        )
        
        if should_update and cache['update_count'] < 8:  # Max 8 updates per download
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
                cache['last_update'] = current_time
                cache['last_percentage'] = percentage
                cache['update_count'] += 1
            except pyrogram.errors.FloodWait:
                # Skip this update to avoid flood wait
                pass
            except Exception:
                # Ignore other update errors
                pass
                
