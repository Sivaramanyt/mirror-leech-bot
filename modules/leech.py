import asyncio
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from downloaders.terabox import TeraboxDownloader
from utils.helpers import get_readable_file_size, is_supported_url
from utils.progress import ProgressTracker
from utils.database import db

# NEW IMPORTS - Add these to your existing imports
from utils.verification import verification_manager
from utils.file_manager import file_manager

logger = logging.getLogger(__name__)

class LeechManager:
    def __init__(self):
        self.active_downloads = {}
        self.terabox_downloader = TeraboxDownloader()
        self.progress_tracker = ProgressTracker()
    
    async def handle_leech_request(self, client: Client, message: Message):
        """Handle leech request with verification and forwarding"""
        try:
            user_id = message.from_user.id
            
            # NEW: Verification check (File Store Bot method)
            verification_needed = await verification_manager.check_user_verification(user_id)
            
            if verification_needed:
                verification_link = await verification_manager.generate_verification_link(user_id)
                await message.reply_text(
                    f"🔐 **Verification Required**\n\n"
                    f"You have used your 3 free downloads. Please complete verification to continue:\n\n"
                    f"🔗 **Verification Link:** {verification_link}\n\n"
                    f"After verification, you can use the bot for the time period set by admin.\n\n"
                    f"⏰ Contact admin if you have issues with verification."
                )
                return
            
            # Check if URL provided
            if len(message.command) < 2:
                await message.reply_text(
                    "❌ **Please provide a URL to download**\n\n"
                    "**Usage:** `/leech [URL]`\n"
                    "**Example:** `/leech https://terabox.com/s/abc123`"
                )
                return
            
            url = message.command[1]
            
            # Validate URL
            if not is_supported_url(url):
                await message.reply_text(
                    "❌ **Unsupported URL**\n\n"
                    "**Supported platforms:**\n"
                    "• Terabox\n"
                    "• Direct download links"
                )
                return
            
            # Check if user already has active download
            if user_id in self.active_downloads:
                await message.reply_text(
                    "⚠️ **You already have an active download**\n\n"
                    "Please wait for it to complete before starting a new one."
                )
                return
            
            # Add to active downloads
            self.active_downloads[user_id] = {
                "url": url,
                "message": message,
                "status": "starting"
            }
            
            # Send initial status message
            status_msg = await message.reply_text(
                "🚀 **Starting download...**\n\n"
                f"📎 **URL:** `{url[:50]}...`\n"
                f"👤 **User:** {message.from_user.mention}\n"
                f"⏳ **Status:** Initializing..."
            )
            
            # Update active download info
            self.active_downloads[user_id]["status_msg"] = status_msg
            
            try:
                # Start download process
                await self._process_download(client, message, url, user_id, status_msg)
                
            except Exception as download_error:
                logger.error(f"❌ Download error for user {user_id}: {download_error}")
                await status_msg.edit_text(
                    f"❌ **Download Failed**\n\n"
                    f"**Error:** {str(download_error)}\n\n"
                    f"Please try again or contact admin if the issue persists."
                )
            finally:
                # Remove from active downloads
                if user_id in self.active_downloads:
                    del self.active_downloads[user_id]
        
        except Exception as e:
            logger.error(f"❌ Error in leech request handler: {e}")
            await message.reply_text(f"❌ **An error occurred:** {str(e)}")
    
    async def _process_download(self, client: Client, message: Message, url: str, user_id: int, status_msg: Message):
        """Process the actual download"""
        try:
            # Update status
            await status_msg.edit_text(
                "📥 **Downloading file...**\n\n"
                f"📎 **URL:** `{url[:50]}...`\n"
                f"⚡ **Status:** Extracting file information..."
            )
            
            # Create progress callback
            async def progress_callback(downloaded: int, total: int, task_id: str):
                try:
                    if total > 0:
                        percentage = (downloaded / total) * 100
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        
                        progress_text = (
                            f"📥 **Downloading...**\n\n"
                            f"📊 **Progress:** {percentage:.1f}%\n"
                            f"📦 **Downloaded:** {downloaded_mb:.1f} MB\n"
                            f"📋 **Total:** {total_mb:.1f} MB\n"
                            f"⚡ **Speed:** Lightning-fast!"
                        )
                        
                        # Update every 2MB to avoid flood limits
                        if downloaded % (2 * 1024 * 1024) < (128 * 1024):  # Every 2MB
                            await status_msg.edit_text(progress_text)
                except Exception as progress_error:
                    logger.error(f"Progress update error: {progress_error}")
            
            # Download the file
            if "terabox" in url.lower() or any(domain in url.lower() for domain in [
                "nephobox", "4funbox", "mirrobox", "momerybox", "teraboxapp", 
                "1024tera", "gibibox", "goaibox", "terasharelink", "teraboxlink"
            ]):
                downloaded_file = await self.terabox_downloader.download(
                    url, progress_callback, f"download_{user_id}"
                )
            else:
                # Handle other download types here if needed
                await status_msg.edit_text("❌ **Unsupported URL type**")
                return
            
            if not downloaded_file or not os.path.exists(downloaded_file):
                await status_msg.edit_text(
                    "❌ **Download failed**\n\n"
                    "The file could not be downloaded. Please check the URL and try again."
                )
                return
            
            # Get file info
            file_size = os.path.getsize(downloaded_file)
            filename = os.path.basename(downloaded_file)
            
            await status_msg.edit_text(
                f"✅ **Download completed!**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                f"📤 **Status:** Forwarding to channel..."
            )
            
            # NEW: Forward to private channel anonymously
            try:
                channel_msg_id = await file_manager.forward_to_channel(
                    downloaded_file, 
                    filename,
                    client
                )
                
                if channel_msg_id:
                    # Schedule auto-delete (24 hours default)
                    await file_manager.schedule_auto_delete(
                        downloaded_file, 
                        filename, 
                        channel_msg_id, 
                        24  # 24 hours
                    )
                    logger.info(f"📤 File forwarded to channel: {filename}")
                
            except Exception as forward_error:
                logger.error(f"❌ Error forwarding to channel: {forward_error}")
                # Continue with sending to user even if forwarding fails
            
            # Send file to user
            await status_msg.edit_text(
                f"📤 **Uploading to you...**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                f"⚡ **Status:** Preparing upload..."
            )
            
            # Determine file type and send accordingly
            file_extension = os.path.splitext(filename.lower())[1]
            
            try:
                if file_extension in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
                    # Send as video
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=downloaded_file,
                        caption=(
                            f"📹 **Video Download Complete**\n\n"
                            f"📁 **Filename:** `{filename}`\n"
                            f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                            f"⚡ **Downloaded by:** @{client.me.username}\n\n"
                            f"🚀 **Lightning-fast Terabox downloads!**"
                        ),
                        supports_streaming=True,
                        reply_to_message_id=message.id
                    )
                    logger.info(f"📹 Video uploaded to user {user_id}: {filename}")
                    
                elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                    # Send as photo
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=downloaded_file,
                        caption=(
                            f"🖼️ **Image Download Complete**\n\n"
                            f"📁 **Filename:** `{filename}`\n"
                            f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                            f"⚡ **Downloaded by:** @{client.me.username}"
                        ),
                        reply_to_message_id=message.id
                    )
                    logger.info(f"🖼️ Image uploaded to user {user_id}: {filename}")
                    
                else:
                    # Send as document
                    await client.send_document(
                        chat_id=message.chat.id,
                        document=downloaded_file,
                        caption=(
                            f"📄 **File Download Complete**\n\n"
                            f"📁 **Filename:** `{filename}`\n"
                            f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                            f"⚡ **Downloaded by:** @{client.me.username}"
                        ),
                        reply_to_message_id=message.id
                    )
                    logger.info(f"📄 Document uploaded to user {user_id}: {filename}")
                
                # Delete status message after successful upload
                try:
                    await status_msg.delete()
                except:
                    pass
                
                # Log successful completion
                logger.info(f"✅ Download completed successfully for user {user_id}: {filename}")
                
            except Exception as upload_error:
                logger.error(f"❌ Upload error for user {user_id}: {upload_error}")
                await status_msg.edit_text(
                    f"❌ **Upload failed**\n\n"
                    f"The file was downloaded but couldn't be uploaded. "
                    f"This might be due to file size limits or network issues."
                )
            
            # Clean up local file
            try:
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                    logger.info(f"🗑️ Local file cleaned up: {downloaded_file}")
            except Exception as cleanup_error:
                logger.error(f"❌ Cleanup error: {cleanup_error}")
                
        except Exception as process_error:
            logger.error(f"❌ Process download error: {process_error}")
            raise process_error
    
    async def get_active_downloads(self) -> dict:
        """Get currently active downloads"""
        return self.active_downloads.copy()
    
    async def cancel_download(self, user_id: int) -> bool:
        """Cancel a user's active download"""
        if user_id in self.active_downloads:
            try:
                download_info = self.active_downloads[user_id]
                if "status_msg" in download_info:
                    await download_info["status_msg"].edit_text("❌ **Download cancelled**")
                del self.active_downloads[user_id]
                logger.info(f"🚫 Download cancelled for user {user_id}")
                return True
            except Exception as e:
                logger.error(f"❌ Error cancelling download for user {user_id}: {e}")
        return False
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.terabox_downloader.close()
            logger.info("🧹 LeechManager cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

# Initialize leech manager
leech_manager = LeechManager()

# Command handlers
@Client.on_message(filters.command("leech"))
async def leech_command(client: Client, message: Message):
    """Handle leech command"""
    await leech_manager.handle_leech_request(client, message)

@Client.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    """Cancel active download"""
    user_id = message.from_user.id
    success = await leech_manager.cancel_download(user_id)
    
    if success:
        await message.reply_text("✅ **Download cancelled successfully**")
    else:
        await message.reply_text("❌ **No active download to cancel**")

@Client.on_message(filters.command("status"))
async def status_command(client: Client, message: Message):
    """Check download status"""
    user_id = message.from_user.id
    active_downloads = await leech_manager.get_active_downloads()
    
    if user_id in active_downloads:
        download_info = active_downloads[user_id]
        status_text = (
            f"📊 **Your Download Status**\n\n"
            f"📎 **URL:** `{download_info['url'][:50]}...`\n"
            f"⚡ **Status:** {download_info.get('status', 'Processing')}\n"
            f"🕐 **Started:** Just now"
        )
        await message.reply_text(status_text)
    else:
        await message.reply_text("❌ **No active downloads**")

# Cleanup on shutdown
async def cleanup_leech_manager():
    """Cleanup function to be called on shutdown"""
    await leech_manager.cleanup()
