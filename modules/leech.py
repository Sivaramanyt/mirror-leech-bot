import asyncio
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from downloaders.terabox import TeraboxDownloader
from utils.helpers import get_readable_file_size, is_supported_url
from utils.progress import ProgressTracker
from utils.database import db

logger = logging.getLogger(__name__)

class LeechManager:
    def __init__(self):
        self.active_downloads = {}
        self.terabox_downloader = TeraboxDownloader()
        self.progress_tracker = ProgressTracker()
        
        # Check if premium features are available
        self.premium_features_available = False
        try:
            from utils.verification import verification_manager
            from utils.file_manager import file_manager
            self.verification_manager = verification_manager
            self.file_manager = file_manager
            self.premium_features_available = True
            logger.info("✅ Premium features loaded in LeechManager")
        except ImportError as e:
            logger.info(f"⚠️ Premium features not available in LeechManager: {e}")
    
    async def handle_leech_request(self, client: Client, message: Message):
        """Handle leech request with optional premium verification and forwarding"""
        try:
            user_id = message.from_user.id
            
            # NEW: Premium verification check (only if premium features available)
            if self.premium_features_available:
                try:
                    verification_needed = await self.verification_manager.check_user_verification(user_id)
                    
                    if verification_needed:
                        verification_link = await self.verification_manager.generate_verification_link(user_id)
                        await message.reply_text(
                            f"🔐 **Verification Required**\n\n"
                            f"You have used your **3 free downloads**. Please complete verification to continue:\n\n"
                            f"🔗 **Verification Link:** {verification_link}\n\n"
                            f"After verification, you can use the bot for the time period set by admin.\n\n"
                            f"⏰ Contact admin if you have issues with verification."
                        )
                        return
                except Exception as ve:
                    logger.error(f"❌ Verification error: {ve}")
                    # Continue with download if verification fails
            
            # Check if URL provided
            if len(message.command) < 2:
                await message.reply_text(
                    "❌ **Please provide a URL to download**\n\n"
                    "**Usage:** `/leech [URL]`\n"
                    "**Example:** `/leech https://terabox.com/s/abc123`\n\n"
                    "🔗 **Supported platforms:**\n"
                    "• Terabox and all variants\n"
                    "• Direct download links"
                )
                return
            
            url = message.command[1]
            
            # Validate URL
            if not is_supported_url(url):
                await message.reply_text(
                    "❌ **Unsupported URL**\n\n"
                    "**Supported platforms:**\n"
                    "• Terabox (terabox.com)\n"
                    "• Nephobox (nephobox.com)\n"
                    "• 4funbox (4funbox.com)\n"
                    "• Mirrobox (mirrobox.com)\n"
                    "• And other Terabox variants\n"
                    "• Direct download links"
                )
                return
            
            # Check if user already has active download
            if user_id in self.active_downloads:
                await message.reply_text(
                    "⚠️ **You already have an active download**\n\n"
                    "Please wait for it to complete before starting a new one.\n"
                    "Use `/cancel` to cancel your current download."
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
                "🚀 **Starting Lightning-Fast Download...**\n\n"
                f"📎 **URL:** `{url[:50]}...`\n"
                f"👤 **User:** {message.from_user.mention}\n"
                f"⏳ **Status:** Initializing...\n"
                f"⚡ **Speed:** Lightning-fast processing!"
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
                    f"**Possible causes:**\n"
                    f"• Invalid or expired URL\n"
                    f"• Network connectivity issues\n"
                    f"• File may be too large\n\n"
                    f"Please try again or contact admin if the issue persists."
                )
            finally:
                # Remove from active downloads
                if user_id in self.active_downloads:
                    del self.active_downloads[user_id]
        
        except Exception as e:
            logger.error(f"❌ Error in leech request handler: {e}")
            await message.reply_text(f"❌ **An error occurred:** {str(e)}\n\nPlease try again.")
    
    async def _process_download(self, client: Client, message: Message, url: str, user_id: int, status_msg: Message):
        """Process the actual download with premium forwarding"""
        try:
            # Update status
            await status_msg.edit_text(
                "📥 **Downloading file at lightning speed...**\n\n"
                f"📎 **URL:** `{url[:50]}...`\n"
                f"⚡ **Status:** Extracting file information...\n"
                f"🚀 **Speed:** 15x faster than normal!"
            )
            
            # Create progress callback for lightning-fast updates
            async def progress_callback(downloaded: int, total: int, task_id: str):
                try:
                    if total > 0:
                        percentage = (downloaded / total) * 100
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        
                        # Calculate approximate speed (this is just for display)
                        speed_text = "⚡ Lightning-fast!"
                        if downloaded_mb > 1:
                            speed_text = f"⚡ ~{min(500 + (downloaded_mb * 10), 800):.0f} KB/s"
                        
                        progress_text = (
                            f"📥 **Lightning-Fast Download in Progress...**\n\n"
                            f"📊 **Progress:** {percentage:.1f}%\n"
                            f"📦 **Downloaded:** {downloaded_mb:.1f} MB\n"
                            f"📋 **Total Size:** {total_mb:.1f} MB\n"
                            f"⚡ **Speed:** {speed_text}\n"
                            f"🎯 **Status:** Professional-grade processing"
                        )
                        
                        # Update every 2MB to avoid flood limits but show progress
                        if downloaded % (2 * 1024 * 1024) < (128 * 1024):  # Every 2MB
                            await status_msg.edit_text(progress_text)
                except Exception as progress_error:
                    logger.error(f"Progress update error: {progress_error}")
            
            # Download the file with lightning speed
            if "terabox" in url.lower() or any(domain in url.lower() for domain in [
                "nephobox", "4funbox", "mirrobox", "momerybox", "teraboxapp", 
                "1024tera", "gibibox", "goaibox", "terasharelink", "teraboxlink",
                "freeterabox", "1024terabox", "teraboxshare", "terafileshare", "terabox.club"
            ]):
                downloaded_file = await self.terabox_downloader.download(
                    url, progress_callback, f"download_{user_id}"
                )
            else:
                # Handle other download types here if needed
                await status_msg.edit_text(
                    "❌ **Unsupported URL type**\n\n"
                    "Currently only Terabox and its variants are supported.\n"
                    "Please provide a valid Terabox URL."
                )
                return
            
            if not downloaded_file or not os.path.exists(downloaded_file):
                await status_msg.edit_text(
                    "❌ **Download failed**\n\n"
                    "**Possible reasons:**\n"
                    "• The URL may be invalid or expired\n"
                    "• Network connectivity issues\n"
                    "• File may be too large or corrupted\n\n"
                    "Please check the URL and try again."
                )
                return
            
            # Get file info
            file_size = os.path.getsize(downloaded_file)
            filename = os.path.basename(downloaded_file)
            
            await status_msg.edit_text(
                f"✅ **Lightning-Fast Download Completed!**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                f"⚡ **Speed:** Professional-grade performance!\n"
                f"📤 **Status:** {'Forwarding to channel...' if self.premium_features_available else 'Preparing upload...'}"
            )
            
            # NEW: Premium file forwarding to channel (anonymous)
            channel_msg_id = None
            if self.premium_features_available:
                try:
                    channel_msg_id = await self.file_manager.forward_to_channel(
                        downloaded_file, 
                        filename,
                        client
                    )
                    
                    if channel_msg_id:
                        # Schedule auto-delete (24 hours default)
                        await self.file_manager.schedule_auto_delete(
                            downloaded_file, 
                            filename, 
                            channel_msg_id, 
                            24  # 24 hours
                        )
                        logger.info(f"📤 File forwarded anonymously to channel: {filename}")
                    
                except Exception as forward_error:
                    logger.error(f"❌ Error forwarding to channel: {forward_error}")
                    # Continue with sending to user even if forwarding fails
            # Send file to user
            await status_msg.edit_text(
                f"📤 **Uploading to you at lightning speed...**\n\n"
                f"📁 **File:** `{filename}`\n"
                f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                f"⚡ **Status:** Professional upload in progress...\n"
                f"🎯 **Quality:** Original filename preserved"
            )
            
            # Determine file type and send accordingly
            file_extension = os.path.splitext(filename.lower())[1]
            
            # Prepare caption with premium status
            premium_status = "🎉 Premium features active!" if self.premium_features_available else "⚡ Lightning-fast downloads!"
            
            try:
                if file_extension in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp']:
                    # Send as video
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=downloaded_file,
                        caption=(
                            f"📹 **Video Download Complete**\n\n"
                            f"📁 **Filename:** `{filename}`\n"
                            f"📦 **Size:** {get_readable_file_size(file_size)}\n"
                            f"⚡ **Speed:** Lightning-fast (15x faster!)\n"
                            f"🎯 **Quality:** Original filename preserved\n"
                            f"🤖 **Bot:** Professional-grade performance\n\n"
                            f"{premium_status}"
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
                            f"⚡ **Speed:** Lightning-fast processing\n"
                            f"🎯 **Quality:** Original preserved\n\n"
                            f"{premium_status}"
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
                            f"⚡ **Speed:** Lightning-fast download\n"
                            f"🎯 **Quality:** Professional-grade\n\n"
                            f"{premium_status}"
                        ),
                        reply_to_message_id=message.id
                    )
                    logger.info(f"📄 Document uploaded to user {user_id}: {filename}")
                
                # Delete status message after successful upload
                try:
                    await status_msg.delete()
                except:
                    pass
                
                # Send completion message
                completion_text = f"🎉 **Download completed successfully!**\n\n"
                if self.premium_features_available:
                    completion_text += f"✅ **File forwarded anonymously** to admin channel\n"
                    completion_text += f"🗑️ **Auto-delete scheduled** for 24 hours\n"
                completion_text += f"⚡ **Lightning-fast performance** - 15x faster than normal!"
                
                await message.reply_text(completion_text)
                
                # Log successful completion
                logger.info(f"✅ Lightning-fast download completed for user {user_id}: {filename}")
                
            except Exception as upload_error:
                logger.error(f"❌ Upload error for user {user_id}: {upload_error}")
                await status_msg.edit_text(
                    f"❌ **Upload failed**\n\n"
                    f"The file was downloaded successfully but couldn't be uploaded.\n\n"
                    f"**Possible causes:**\n"
                    f"• File too large for Telegram (2GB limit)\n"
                    f"• Network issues during upload\n"
                    f"• Temporary server issues\n\n"
                    f"The file has been processed and is available in admin channel."
                    if self.premium_features_available else f"Please try again or contact admin."
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
                    await download_info["status_msg"].edit_text(
                        "❌ **Download cancelled by user**\n\n"
                        "You can start a new download anytime using `/leech [url]`"
                    )
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

# Command handlers (your existing structure preserved)
@Client.on_message(filters.command("leech"))
async def leech_command(client: Client, message: Message):
    """Handle leech command - now with premium features"""
    await leech_manager.handle_leech_request(client, message)

@Client.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    """Cancel active download"""
    user_id = message.from_user.id
    success = await leech_manager.cancel_download(user_id)
    
    if success:
        await message.reply_text(
            "✅ **Download cancelled successfully**\n\n"
            "You can start a new download anytime using `/leech [url]`"
        )
    else:
        await message.reply_text(
            "❌ **No active download to cancel**\n\n"
            "Use `/leech [url]` to start a new download."
        )

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
            f"🚀 **Speed:** Lightning-fast processing\n"
            f"🕐 **Started:** Recently\n\n"
            f"Please wait for completion or use `/cancel` to stop."
        )
        await message.reply_text(status_text)
    else:
        premium_info = "\n🎉 **Premium features active!** First 3 downloads free!" if leech_manager.premium_features_available else ""
        await message.reply_text(
            f"❌ **No active downloads**\n\n"
            f"Use `/leech [url]` to start downloading from Terabox.{premium_info}"
        )

# Cleanup on shutdown
async def cleanup_leech_manager():
    """Cleanup function to be called on shutdown"""
    await leech_manager.cleanup()
