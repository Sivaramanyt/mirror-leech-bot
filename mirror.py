import asyncio
import logging
from pyrogram import Client
from pyrogram.types import Message
from utils.helpers import *
from downloaders.terabox import TeraboxDownloader
from downloaders.youtube import YouTubeDownloader  
from downloaders.direct import DirectDownloader

logger = logging.getLogger(__name__)

class MirrorHandler:
    def __init__(self, bot):
        self.bot = bot

    async def mirror_command(self, client: Client, message: Message):
        """Handle /mirror command"""
        args = message.text.split()

        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:** `/mirror [link]`\n\n"
                "**Examples:**\n"
                "• `/mirror https://terabox.com/s/xxxxx`\n"
                "• `/mirror https://example.com/file.zip`\n"
                "• `/mirror https://drive.google.com/file/d/xxxxx`"
            )
            return

        url = args[1]
        task_id = self.bot.generate_task_id()

        # Determine downloader type
        if is_terabox_link(url):
            downloader = TeraboxDownloader()
        elif is_youtube_link(url):
            downloader = YouTubeDownloader()
        elif is_google_drive_link(url):
            downloader = DirectDownloader()
        else:
            downloader = DirectDownloader()

        # Add task to active tasks
        filename = extract_filename_from_url(url)
        self.bot.active_tasks[task_id] = {
            'name': filename,
            'status': 'starting',
            'progress': 0,
            'user_id': message.from_user.id
        }

        status_msg = await message.reply_text(f"🚀 **Starting download...**\n📁 {filename}")

        try:
            # Start download
            file_path = await downloader.download(url, self.progress_callback, task_id)

            if file_path:
                # Upload to Google Drive if configured
                if self.bot.gdrive_handler:
                    await status_msg.edit_text("☁️ **Uploading to Google Drive...**")
                    result = await self.bot.gdrive_handler.upload_file(file_path)
                    if result:
                        await status_msg.edit_text(
                            f"✅ **Mirror completed!**\n"
                            f"📁 **File:** {result['name']}\n"
                            f"🔗 **Link:** {result['link']}"
                        )
                    else:
                        await status_msg.edit_text("❌ **Upload failed!**")
                else:
                    await status_msg.edit_text("❌ **Google Drive not configured**")
            else:
                await status_msg.edit_text("❌ **Download failed!**")

        except Exception as e:
            logger.error(f"Mirror error: {e}")
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")
        finally:
            # Remove from active tasks
            self.bot.active_tasks.pop(task_id, None)

    async def ytdl_command(self, client: Client, message: Message):
        """Handle /ytdl command"""
        args = message.text.split()

        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:** `/ytdl [link]`\n\n"
                "**Supported sites:** YouTube, Instagram, Twitter, TikTok, and 900+ more!"
            )
            return

        url = args[1]
        task_id = self.bot.generate_task_id()

        downloader = YouTubeDownloader()

        status_msg = await message.reply_text("🎥 **Fetching video info...**")

        try:
            # Get video info first
            info = await downloader.get_video_info(url)
            if not info:
                await status_msg.edit_text("❌ **Failed to get video info**")
                return

            # Add to active tasks
            self.bot.active_tasks[task_id] = {
                'name': info.get('title', 'Unknown'),
                'status': 'downloading', 
                'progress': 0,
                'user_id': message.from_user.id
            }

            await status_msg.edit_text(f"📥 **Downloading:** {info.get('title', 'Unknown')[:50]}...")

            # Download
            file_path = await downloader.download(url, self.progress_callback, task_id)

            if file_path and self.bot.gdrive_handler:
                await status_msg.edit_text("☁️ **Uploading to Google Drive...**")
                result = await self.bot.gdrive_handler.upload_file(file_path)
                if result:
                    await status_msg.edit_text(
                        f"✅ **YT-DL Mirror completed!**\n"
                        f"📁 **File:** {result['name']}\n"
                        f"🔗 **Link:** {result['link']}"
                    )
                else:
                    await status_msg.edit_text("❌ **Upload failed!**")
            else:
                await status_msg.edit_text("❌ **Download failed!**")

        except Exception as e:
            logger.error(f"YT-DL error: {e}")
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")
        finally:
            self.bot.active_tasks.pop(task_id, None)

    async def progress_callback(self, current: int, total: int, task_id: str):
        """Progress callback for downloads"""
        if task_id in self.bot.active_tasks:
            progress = (current / total) * 100 if total > 0 else 0
            self.bot.active_tasks[task_id]['progress'] = progress
