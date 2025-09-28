import re
import asyncio
import logging
from pyrogram import filters, Client
from pyrogram.types import Message
from utils.database import get_user_downloads, update_user_downloads, is_user_verified
from utils.config import FREE_DOWNLOAD_LIMIT, IS_VERIFY
from utils.terabox import terabox_downloader

logger = logging.getLogger(__name__)

def setup_message_handlers(app: Client):
    """Setup message handlers with FULL URL support"""
    
    # ✅ COMPLETE URL VALIDATOR (INCLUDES teraboxlink.com)
    def is_supported_terabox_url(url: str) -> bool:
        """Complete Terabox URL validator"""
        try:
            url = url.strip().lower()
            
            # ALL Terabox domain patterns
            patterns = [
                r'terabox\.com',
                r'terasharelink\.com', 
                r'teraboxlink\.com',      # ← THIS WAS MISSING!
                r'nephobox\.com',
                r'4funbox\.com',
                r'mirrobox\.com',
                r'momerybox\.com',
                r'tibibox\.com',
                r'1024tera\.com',
                r'teraboxapp\.com',
                r'terabox\.app',
                r'gibibox\.com',
                r'goaibox\.com',
                r'freeterabox\.com',
                r'1024terabox\.com',
                r'teraboxshare\.com',
                r'terafileshare\.com',
                r'terabox\.club',
                r'dubox\.com',
                r'app\.dubox\.com'
            ]
            
            # Check if URL matches any pattern
            for pattern in patterns:
                if re.search(pattern, url):
                    # Must have /s/ path or surl parameter
                    if '/s/' in url or 'surl=' in url:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return False

    @app.on_message(filters.text & filters.private & ~filters.command)
    async def handle_url_message(client: Client, message: Message):
        """Handle URL messages with complete domain support"""
        try:
            url = message.text.strip()
            user_id = message.from_user.id
            
            # Log the attempt
            logger.info(f"📨 Message from user {user_id}: {url[:50]}...")
            
            # ✅ ENHANCED: Check if it's a supported Terabox URL
            if not is_supported_terabox_url(url):
                # Only show error if it looks like a URL
                if any(indicator in url.lower() for indicator in ['http://', 'https://', 'www.', '.com', '.net', '.org']):
                    await message.reply(
                        "⚠️ **URL Not Supported**\n\n"
                        "**✅ Supported domains:**\n"
                        "• terabox.com\n"
                        "• terasharelink.com\n"
                        "• teraboxlink.com ✅\n"  # ← NOW SHOWN AS SUPPORTED
                        "• nephobox.com\n"
                        "• 4funbox.com\n" 
                        "• mirrobox.com\n"
                        "• And other Terabox variants\n\n"
                        "Please send a valid Terabox share link."
                    )
                return
            
            # ✅ URL IS SUPPORTED - Continue with download logic
            logger.info(f"✅ Valid Terabox URL detected: {url[:50]}...")
            
            # Verification check (if enabled)
            if IS_VERIFY and not await is_user_verified(user_id):
                await message.reply(
                    "🔐 **Verification Required**\n\n"
                    "Please complete verification first using /verify command."
                )
                return
            
            # Download limit check
            user_downloads = await get_user_downloads(user_id)
            if user_downloads >= FREE_DOWNLOAD_LIMIT:
                await message.reply(
                    f"📊 **Download Limit Reached**\n\n"
                    f"You have used {user_downloads}/{FREE_DOWNLOAD_LIMIT} free downloads.\n"
                    f"Upgrade to premium for unlimited downloads."
                )
                return
            
            # Start download process
            status_message = await message.reply("📥 **Starting download...**\n⏳ Please wait...")
            
            try:
                # Progress callback function
                async def progress_callback(downloaded: int, total: int, speed: float):
                    try:
                        if total > 0:
                            percentage = (downloaded / total) * 100
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total / (1024 * 1024)
                            
                            progress_text = (
                                f"📥 **Downloading...**\n"
                                f"📊 Progress: {percentage:.1f}%\n"
                                f"📦 Size: {downloaded_mb:.1f} MB / {total_mb:.1f} MB\n"
                                f"⚡ Speed: {speed:.1f} MB/min"
                            )
                            
                            await status_message.edit_text(progress_text)
                    except Exception as e:
                        logger.warning(f"Progress update error: {e}")
                
                # Download the file
                downloaded_file = await terabox_downloader.download_file(url, progress_callback)
                
                if downloaded_file:
                    await status_message.edit_text("📤 **Uploading to Telegram...**")
                    
                    # Upload to Telegram
                    await message.reply_document(
                        document=downloaded_file,
                        caption=f"✅ **Download Complete**\n🔗 Source: Terabox\n🤖 Bot: @{client.me.username}"
                    )
                    
                    # Update user download count
                    await update_user_downloads(user_id, user_downloads + 1)
                    
                    # Clean up
                    try:
                        import os
                        os.remove(downloaded_file)
                    except:
                        pass
                    
                    await status_message.delete()
                    
                else:
                    await status_message.edit_text(
                        "❌ **Download Failed**\n\n"
                        "The file could not be downloaded. Please try again or contact support."
                    )
                    
            except Exception as e:
                logger.error(f"Download error: {e}")
                await status_message.edit_text(
                    "❌ **Download Error**\n\n"
                    f"An error occurred: {str(e)[:100]}..."
                )
                
        except Exception as e:
            logger.error(f"Message handler error: {e}")
            await message.reply("❌ An unexpected error occurred. Please try again.")

    logger.info("✅ Message handlers setup complete with FULL URL support")
        
