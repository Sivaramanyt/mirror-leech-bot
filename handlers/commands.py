import time
import logging
import os
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import validators

logger = logging.getLogger(__name__)

def setup_command_handlers(app):
    """Compact command handlers with ultra-fast downloads"""
    
    @app.on_message(filters.command("start"))
    async def start_command(client, message: Message):
        start_text = f"""
🚀 **Lightning-Fast Terabox Leech Bot**

Hello {message.from_user.mention}! ⚡

📥 **Commands:**
• `/leech [url]` - Ultra-fast download
• `/ping` - Speed test
• `/help` - All supported sites

🔥 **Features:**
• Lightning-fast 8MB chunks
• Smart media upload (video/audio/photo)
• All Terabox variants supported
• Real-time speed tracking

⚡ **Ready for ultra-fast downloads!**
        """
        
        keyboard = [[
            InlineKeyboardButton("📋 Help", callback_data="help"),
            InlineKeyboardButton("🏓 Ping", callback_data="ping")
        ]]
        
        await message.reply_text(start_text, reply_markup=InlineKeyboardMarkup(keyboard))
        logger.info(f"📥 Start command from user {message.from_user.id}")

    @app.on_message(filters.command("ping"))
    async def ping_command(client, message: Message):
        start_time = time.time()
        msg = await message.reply_text("🏓 Testing speed...")
        ping_time = round((time.time() - start_time) * 1000, 2)
        
        await msg.edit_text(
            f"⚡ **Ultra-Fast Bot Ready!**\n\n"
            f"🏓 **Ping:** {ping_time}ms\n"
            f"🚀 **Status:** Online\n"
            f"⚡ **Speed Mode:** 8MB chunks\n"
            f"📊 **Downloads:** Ultra-fast"
        )

    @app.on_message(filters.command("help"))
    async def help_command(client, message: Message):
        await message.reply_text("""
⚡ **ULTRA-FAST TERABOX LEECH BOT**

📥 **Usage:**
• `/leech [url]` - Ultra-fast download
• Send Terabox URL directly

🌐 **Supported Sites:**
• terabox.com, terasharelink.com
• nephobox.com, 4funbox.com
• mirrobox.com, and 5+ more variants

⚡ **Speed Features:**
• 8MB chunks for maximum speed
• Smart retry with 2-second delays
• Real-time speed tracking (MB/min)
• 50 concurrent connections

🎯 **Smart Upload:**
• 🎥 Videos → Video media
• 🎵 Audio → Audio player  
• 🖼️ Photos → Photo gallery
• 📄 Others → Documents

**Ready for lightning-fast downloads!** 🚀
        """)

    @app.on_message(filters.command("leech"))
    async def leech_command(client, message: Message):
        try:
            user_id = message.from_user.id
            
            if len(message.command) < 2:
                await message.reply_text(
                    "❌ **Please provide a Terabox URL**\n\n"
                    "**Usage:** `/leech [URL]`\n"
                    "**Example:** `/leech https://terabox.com/s/abc123`\n\n"
                    "⚡ **Features:** Ultra-fast 8MB chunks, smart media upload"
                )
                return
            
            url = " ".join(message.command[1:])
            
            if not validators.url(url):
                await message.reply_text("❌ **Invalid URL format**\n\nExample: `https://terabox.com/s/abc123`")
                return
            
            # Supported domains
            supported_domains = [
                'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
                'momerybox.com', 'teraboxapp.com', '1024tera.com', 'gibibox.com',
                'goaibox.com', 'terasharelink.com'
            ]
            
            if not any(domain in url.lower() for domain in supported_domains):
                await message.reply_text(f"⚠️ **URL Not Supported**\n\nSupported: terabox.com, terasharelink.com, nephobox.com, etc.")
                return
            
            # Extract share code
            import re
            surl_match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
            if not surl_match:
                await message.reply_text("❌ **Invalid Terabox URL**\n\nFormat: `https://terabox.com/s/shareCode`")
                return
            
            surl = surl_match.group(1)
            status_msg = await message.reply_text("⚡ **Starting ultra-fast download...**")
            
            try:
                from utils.terabox import terabox_downloader
                
                await status_msg.edit_text("📊 **Getting file info...**")
                file_info = await terabox_downloader.extract_file_info(url)
                
                if not file_info.get("success"):
                    await status_msg.edit_text(f"❌ **Error:** {file_info.get('error')}")
                    return
                
                filename = file_info['filename']
                await status_msg.edit_text(
                    f"✅ **File Found!**\n\n"
                    f"📁 **Name:** {filename}\n"
                    f"⚡ **Starting ultra-fast download...**"
                )
                
                # Ultra-fast progress callback with speed
                async def progress_callback(downloaded, total, speed_mbps=0):
                    try:
                        if total > 0:
                            progress = (downloaded / total) * 100
                            downloaded_mb = downloaded / (1024 * 1024)
                            total_mb = total / (1024 * 1024)
                            
                            speed_text = f" - {speed_mbps:.1f} MB/min" if speed_mbps > 0 else ""
                            
                            await status_msg.edit_text(
                                f"⚡ **ULTRA-FAST Download**\n\n"
                                f"📁 **File:** {filename[:25]}...\n"
                                f"📊 **Progress:** {progress:.1f}%\n"
                                f"⬇️ **Downloaded:** {downloaded_mb:.1f}/{total_mb:.1f} MB\n"
                                f"🚀 **Speed:** Lightning{speed_text}"
                            )
                    except:
                        pass
                
                # Download with ultra-fast mode
                download_path = await terabox_downloader.download_file(url, progress_callback)
                
                if download_path and os.path.exists(download_path):
                    file_size = os.path.getsize(download_path)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    await status_msg.edit_text(
                        f"📤 **Uploading...**\n\n"
                        f"📁 **File:** {filename}\n"
                        f"📊 **Size:** {file_size_mb:.1f} MB\n"
                        f"🚀 **Status:** Smart media upload..."
                    )
                    
                    # Smart media upload
                    try:
                        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
                        
                        if file_ext in ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', '3gp', 'm4v']:
                            await message.reply_video(
                                video=download_path,
                                caption=f"🎥 **{filename}**\n\n🔗 **Source:** Terabox\n📊 **Size:** {file_size_mb:.1f} MB\n⚡ **Bot:** @Terabox_leech_pro_bot",
                                reply_to_message_id=message.id,
                                supports_streaming=True
                            )
                        elif file_ext in ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma']:
                            await message.reply_audio(
                                audio=download_path,
                                caption=f"🎵 **{filename}**\n\n🔗 **Source:** Terabox\n📊 **Size:** {file_size_mb:.1f} MB\n⚡ **Bot:** @Terabox_leech_pro_bot",
                                reply_to_message_id=message.id
                            )
                        elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                            await message.reply_photo(
                                photo=download_path,
                                caption=f"🖼️ **{filename}**\n\n🔗 **Source:** Terabox\n📊 **Size:** {file_size_mb:.1f} MB\n⚡ **Bot:** @Terabox_leech_pro_bot",
                                reply_to_message_id=message.id
                            )
                        else:
                            await message.reply_document(
                                document=download_path,
                                caption=f"📄 **{filename}**\n\n🔗 **Source:** Terabox\n📊 **Size:** {file_size_mb:.1f} MB\n⚡ **Bot:** @Terabox_leech_pro_bot",
                                reply_to_message_id=message.id
                            )
                        
                        await status_msg.edit_text("⚡ **Ultra-Fast Download Complete!** 🎉")
                        
                    except Exception as upload_error:
                        await status_msg.edit_text(f"❌ **Upload Failed:** {str(upload_error)[:100]}...")
                    
                    # Cleanup
                    try:
                        os.remove(download_path)
                        logger.info(f"🗑️ Cleaned up: {download_path}")
                    except:
                        pass
                        
                else:
                    await status_msg.edit_text("❌ **Download failed**")
                
                logger.info(f"⚡ Ultra-fast leech completed for user {user_id}: {filename}")
                    
            except ImportError:
                await status_msg.edit_text(
                    f"⚠️ **Download Module Missing**\n\n"
                    f"✅ **URL Detected:** Terabox Family\n"
                    f"🔑 **Share Code:** `{surl}`\n\n"
                    f"**URL parsing working perfectly!** ✅"
                )
            
        except Exception as e:
            logger.error(f"❌ Leech error: {e}")
            await message.reply_text("❌ **Error occurred** - Please try again")

    # Handle direct URLs
    @app.on_message(filters.text & filters.private & ~filters.command(["start", "help", "ping", "leech"]))
    async def handle_direct_links(client, message: Message):
        url = message.text.strip()
        
        if not validators.url(url):
            await message.reply_text(
                "👋 **Ultra-Fast Terabox Leech Bot**\n\n"
                "🔗 Send me a Terabox URL for lightning-fast download\n"
                "⚡ Features: 8MB chunks, smart media, real-time speed\n\n"
                "Use `/leech [url]` or just send the URL directly!"
            )
            return
        
        supported_domains = [
            'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
            'momerybox.com', 'teraboxapp.com', '1024tera.com', 'gibibox.com',
            'goaibox.com', 'terasharelink.com'
        ]
        
        if any(domain in url.lower() for domain in supported_domains):
            await message.reply_text("⚡ **Direct URL Detected!**\n\n🚀 **Processing ultra-fast download...**")
            
            # Process as leech
            fake_message = message
            fake_message.command = ["leech", url]
            await leech_command(client, fake_message)
        else:
            await message.reply_text(
                f"⚠️ **URL Not Supported**\n\n"
                f"**Supported:** terabox.com, terasharelink.com, nephobox.com, etc.\n\n"
                f"⚡ **Ultra-fast downloads** with smart media upload!"
            )
    
    logger.info("⚡ Ultra-fast command handlers setup complete")
