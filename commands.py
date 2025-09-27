import time
import logging
import os
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import psutil
import validators
from utils.terabox import extract_terabox_info, format_file_size, get_file_type_emoji
from utils.leech import leech_engine
from utils.mirror import mirror_engine
from utils.downloader import universal_downloader
from utils.database import db
from utils.config import TERABOX_DOMAINS, OWNER_ID
from utils.helpers import get_readable_file_size, create_safe_slug

logger = logging.getLogger(__name__)

def setup_command_handlers(app):
    """Setup all command handlers"""
    
    @app.on_message(filters.command("start"))
    async def start_command(client, message: Message):
        """Enhanced start command with comprehensive welcome"""
        user_mention = message.from_user.mention
        user_id = message.from_user.id
        username = message.from_user.username or "Unknown"
        
        # Add user to database
        if db.enabled:
            await db.add_user(user_id, username, message.from_user.first_name)
            await db.update_user_activity(user_id)
        
        start_text = f"""
🚀 **Welcome to Lightning-Fast Mirror Leech Bot!**

Hello {user_mention}! 👋

⚡ **Multi-Platform Downloads:**
• **Terabox** - Lightning-fast downloads
• **YouTube** & 900+ sites via yt-dlp  
• **Direct HTTP/HTTPS** links
• **Google Drive** links (public)
• **Mega** links
• **Telegram files** (forward to bot)

📤 **Upload Destinations:**
• **Telegram** (with auto file splitting)
• **Google Drive** (coming soon)

📋 **Available Commands:**
• `/leech [url]` - Download from supported URLs
• `/mirror [url]` - Download + Upload to Telegram
• `/ytdl [url]` - Download from YouTube/900+ sites
• `/status` - Check bot & system status
• `/mystats` - Your personal statistics
• `/help` - Detailed help & supported sites
• `/ping` - Check bot response time

🔗 **Supported Platforms:**
• **Terabox:** terabox.com, nephobox.com, 4funbox.com
• **Social Media:** YouTube, Instagram, Twitter, TikTok
• **Cloud Storage:** Google Drive, Mega, OneDrive
• **Direct Links:** Any HTTP/HTTPS file URL

🌟 **Features:**
• **Lightning-fast** parallel downloads
• **Auto file splitting** for large files (2GB+)
• **Progress tracking** with real-time updates
• **Smart file detection** with emojis
• **Database logging** for statistics
• **System monitoring** and health checks

🚀 **Ready for lightning-fast downloads!**

Use any command above or just send a supported URL directly!
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 Help & Sites", callback_data="help"),
             InlineKeyboardButton("🏓 Ping Test", callback_data="ping")],
            [InlineKeyboardButton("📊 Bot Stats", callback_data="stats"),
             InlineKeyboardButton("👤 My Stats", callback_data="mystats")],
            [InlineKeyboardButton("❓ About", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(start_text, reply_markup=reply_markup)
        logger.info(f"📥 Start command from user {user_id} (@{username})")

    @app.on_message(filters.command("ping"))
    async def ping_command(client, message: Message):
        """Enhanced ping with comprehensive system stats"""
        start_time = time.time()
        ping_msg = await message.reply_text("🏓 Pinging...")
        end_time = time.time()
        
        ping_time = round((end_time - start_time) * 1000, 2)
        
        # Get comprehensive system stats
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        # Get active downloads/uploads
        active_downloads = len(leech_engine.get_active_downloads())
        active_uploads = len(mirror_engine.get_active_uploads())
        
        ping_text = f"""
🏓 **PONG!**

⚡ **Response Time:** {ping_time}ms
✅ **Bot Status:** Online & Operational

💻 **System Performance:**
• **Memory:** {memory.percent}% used ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)
• **CPU:** {cpu_percent}% usage
• **Disk:** {disk.percent}% used ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)
• **Uptime:** {uptime / 3600:.1f} hours

🔄 **Active Operations:**
• **Downloads:** {active_downloads} active
• **Uploads:** {active_uploads} active

🚀 **All systems operational - Ready for downloads!**
        """
        
        await ping_msg.edit_text(ping_text)

    @app.on_message(filters.command("help"))
    async def help_command(client, message: Message):
        """Comprehensive help with all supported sites"""
        help_text = """
❓ **MIRROR LEECH BOT - COMPREHENSIVE HELP**

📥 **How to Download:**
• Send `/leech [url]` to download only
• Send `/mirror [url]` to download + upload to Telegram
• Send `/ytdl [url]` for YouTube & social media
• Or just **send the URL directly** - bot auto-detects!

⚡ **Quick Commands:**
• `/start` - Welcome & bot info
• `/leech [url]` - Download from URL
• `/mirror [url]` - Download + Upload to Telegram  
• `/ytdl [url]` - YouTube & 900+ sites downloader
• `/status` - Bot system status
• `/mystats` - Your download statistics
• `/cancel` - Cancel active download/upload
• `/ping` - Test bot response time

🌐 **Supported Platforms:**

**🔥 Terabox Family:**
• terabox.com, nephobox.com, 4funbox.com
• mirrobox.com, momerybox.com, teraboxapp.com
• 1024tera.com, gibibox.com, goaibox.com
• terasharelink.com

**📱 Social Media (via yt-dlp):**
• YouTube, YouTube Music
• Instagram (posts, reels, stories)
• Twitter/X (videos, images)
• TikTok (without watermark)
• Facebook (videos, posts)
• Reddit (videos, gifs)
• Pinterest (images, videos)
• LinkedIn (videos)

**🎵 Audio Platforms:**
• SoundCloud, Bandcamp
• Spotify (previews), Apple Music (previews)
• Mixcloud, AudioMack

**📺 Video Platforms:**
• Vimeo, Dailymotion
• Twitch (clips, VODs)
• Rumble, BitChute
• Archive.org

**☁️ Cloud Storage:**
• Google Drive (public links)
• Mega.nz links
• OneDrive (public)
• Dropbox (public)

**🔗 Direct Links:**
• Any HTTP/HTTPS file URL
• Password-protected links
• Streaming URLs (m3u8, mp4, etc.)

💡 **Pro Tips:**
• **Terabox:** Works with private & public links
• **YouTube:** Supports playlists (use /ytdl)
• **Instagram:** Works with private posts (if public)
• **Large Files:** Auto-splits files over 2GB
• **Progress:** Real-time download/upload tracking
• **Quality:** Automatically selects best available

📊 **File Support:**
• **Videos:** MP4, AVI, MKV, MOV, WebM, etc.
• **Audio:** MP3, FLAC, WAV, AAC, OGG, etc.
• **Images:** JPG, PNG, GIF, WebP, etc.
• **Documents:** PDF, DOC, ZIP, RAR, etc.
• **Any file type** supported!

🚀 **Examples:**
/leech https://terabox.com/s/abc123
/mirror https://youtube.com/watch?v=example
/ytdl https://instagram.com/p/example

**Or just send the URL directly - no command needed!**

Ready to download? Send any supported URL! 🔥
        """
        await message.reply_text(help_text)

    @app.on_message(filters.command("status"))
    async def status_command(client, message: Message):
        """Comprehensive bot status"""
        user_id = message.from_user.id
        
        # System stats
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        # Active operations
        active_downloads = leech_engine.get_active_downloads()
        active_uploads = mirror_engine.get_active_uploads()
        user_download = leech_engine.get_user_download(user_id)
        user_upload = mirror_engine.get_user_upload(user_id)
        
        # Database stats
        total_users = await db.get_total_users() if db.enabled else "N/A"
        total_downloads = await db.get_total_downloads() if db.enabled else "N/A"
        
        status_text = f"""
📊 **BOT STATUS REPORT**

✅ **Bot Status:** Online & Operational
🌐 **Uptime:** {psutil.boot_time()}
💾 **Memory:** {memory.percent}% ({memory.available / (1024**3):.1f}GB available)
🖥️ **CPU:** {cpu_percent}%
💿 **Disk:** {disk.percent}% used

📈 **Database Stats:**
• **Total Users:** {total_users}
• **Total Downloads:** {total_downloads}
• **Database:** {"✅ Connected" if db.enabled else "❌ Disabled"}

🔄 **Active Operations:**
• **Global Downloads:** {len(active_downloads)}
• **Global Uploads:** {len(active_uploads)}

👤 **Your Status:**
• **Active Download:** {"✅ Yes" if user_download else "❌ None"}
• **Active Upload:** {"✅ Yes" if user_upload else "❌ None"}
        """
        
        if user_download:
            progress = (user_download['downloaded'] / user_download['total_size']) * 100
            speed = get_readable_file_size(user_download.get('speed', 0)) + "/s"
            status_text += f"\n📥 **Your Download:** {user_download['filename']}\n   Progress: {progress:.1f}% | Speed: {speed}"
        
        if user_upload:
            if 'current_part' in user_upload:
                status_text += f"\n📤 **Your Upload:** {user_upload['filename']}\n   Part: {user_upload['current_part']}/{user_upload['total_parts']}"
            else:
                progress = (user_upload['uploaded'] / user_upload['total_size']) * 100
                speed = get_readable_file_size(user_upload.get('speed', 0)) + "/s"
                status_text += f"\n📤 **Your Upload:** {user_upload['filename']}\n   Progress: {progress:.1f}% | Speed: {speed}"
        
        status_text += "\n\n🚀 **Ready for downloads!**"
        
        await message.reply_text(status_text)

    @app.on_message(filters.command("mystats"))
    async def mystats_command(client, message: Message):
        """User personal statistics"""
        user_id = message.from_user.id
        
        if not db.enabled:
            await message.reply_text(
                "❌ **Statistics Unavailable**\n\n"
                "Database is not configured for this bot.\n"
                "Statistics tracking is disabled."
            )
            return
        
        try:
            user_info = await db.get_user(user_id)
            user_stats = await db.get_user_stats(user_id)
            
            if not user_info:
                await message.reply_text(
                    "❌ **No Data Found**\n\n"
                    "You haven't used the bot yet.\n"
                    "Start downloading to see your statistics!"
                )
                return
            
            join_date = user_info.get('join_date', datetime.now()).strftime('%Y-%m-%d')
            last_activity = user_info.get('last_activity', datetime.now()).strftime('%Y-%m-%d %H:%M')
            
            stats_text = f"""
👤 **YOUR STATISTICS**

📊 **Download Stats:**
• **Total Downloads:** {user_stats['downloads']}
• **Total Data:** {get_readable_file_size(user_stats['total_size'])}
• **Average File Size:** {get_readable_file_size(user_stats['total_size'] / max(user_stats['downloads'], 1))}

📅 **Account Info:**
• **Joined:** {join_date}
• **Last Activity:** {last_activity}
• **User ID:** `{user_id}`
• **Username:** @{user_info.get('username', 'N/A')}

🏆 **Achievements:**
• **Active User:** {'✅' if user_stats['downloads'] > 10 else '❌'} (10+ downloads)
• **Heavy User:** {'✅' if user_stats['downloads'] > 50 else '❌'} (50+ downloads)
• **Power User:** {'✅' if user_stats['downloads'] > 100 else '❌'} (100+ downloads)

🚀 **Keep downloading to unlock more achievements!**
            """
            
            await message.reply_text(stats_text)
            
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            await message.reply_text("❌ Error retrieving your statistics.")

    @app.on_message(filters.command("leech"))
    async def leech_command(client, message: Message):
        """Enhanced leech command for downloading only"""
        try:
            user_id = message.from_user.id
            
            # Check if user has active download
            if leech_engine.get_user_download(user_id):
                await message.reply_text(
                    "⚠️ **Download Already Active**\n\n"
                    "You already have an active download.\n"
                    "Use `/cancel` to cancel it or wait for completion."
                )
                return
            
            # Check URL provided
            if len(message.command) < 2:
                await message.reply_text(
                    "❌ **Please provide a URL to download**\n\n"
                    "**Usage:** `/leech [URL]`\n"
                    "**Examples:**\n"
                    "• `/leech https://terabox.com/s/abc123`\n"
                    "• `/leech https://example.com/file.zip`\n\n"
                    "🔗 **Supported platforms:**\n"
                    "• Terabox and all variants\n"
                    "• Direct HTTP/HTTPS links\n"
                    "• Google Drive, Mega links\n\n"
                    "💡 **Tip:** You can also send URLs directly without `/leech`!"
                )
                return
            
            url = " ".join(message.command[1:])  # Support URLs with spaces
            
            # Validate URL
            if not validators.url(url):
                await message.reply_text(
                    "❌ **Invalid URL Format**\n\n"
                    "Please provide a valid URL starting with http:// or https://\n\n"
                    "**Example:** `https://terabox.com/s/abc123`"
                )
                return
            
            # Update user activity
            if db.enabled:
                await db.update_user_activity(user_id)
            
            # Send processing message
            status_msg = await message.reply_text(
                f"🚀 **Leech Started!**\n\n"
                f"📎 **URL:** `{url[:80]}{'...' if len(url) > 80 else ''}`\n"
                f"👤 **User:** {message.from_user.mention}\n"
                f"⏳ **Status:** Analyzing URL...\n"
                f"🔄 **Please wait...**"
            )
            
            # Progress callback
            async def progress_callback(downloaded, total, speed):
                try:
                    if total > 0:
                        progress = (downloaded / total) * 100
                        await status_msg.edit_text(
                            f"📥 **Downloading...**\n\n"
                            f"📁 **File:** Processing...\n"
                            f"📊 **Progress:** {progress:.1f}%\n"
                            f"⬇️ **Downloaded:** {get_readable_file_size(downloaded)}\n"
                            f"📦 **Total:** {get_readable_file_size(total)}\n"
                            f"⚡ **Speed:** {get_readable_file_size(speed)}/s"
                        )
                except:
                    pass  # Ignore edit errors
            
            # Start leech
            result = await leech_engine.leech_file(message, url, progress_callback=progress_callback)
            
            if result['success']:
                # Success message
                success_text = f"""
✅ **Leech Completed!**

📁 **Filename:** `{result['filename']}`
📊 **Size:** {get_readable_file_size(result['size'])}
⏱️ **Time:** {result.get('download_time', 0):.1f}s
💾 **Saved to:** Downloads folder

🔗 **Next Steps:**
• File is ready for use
• Use `/mirror [url]` to upload to Telegram
• Check `/status` for system info
                """
                
                keyboard = [
                    [InlineKeyboardButton("📤 Mirror This", callback_data=f"mirror_{user_id}")],
                    [InlineKeyboardButton("📊 My Stats", callback_data="mystats"),
                     InlineKeyboardButton("🔄 Leech Another", callback_data="start")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await status_msg.edit_text(success_text, reply_markup=reply_markup)
                
            else:
                # Error message
                await status_msg.edit_text(
                    f"❌ **Leech Failed**\n\n"
                    f"**Error:** {result['error']}\n\n"
                    f"**Possible causes:**\n"
                    f"• Invalid or expired URL\n"
                    f"• Private/restricted file\n"
                    f"• Network connectivity issues\n"
                    f"• Server temporarily unavailable\n\n"
                    f"**Try:**\n"
                    f"• Verify the URL is correct and accessible\n"
                    f"• Try again in a few moments\n"
                    f"• Use a different URL format"
                )
                
            logger.info(f"📥 Leech {'completed' if result['success'] else 'failed'} for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Leech command error: {e}")
            await message.reply_text(
                "❌ **Unexpected Error**\n\n"
                "An unexpected error occurred during the leech process.\n"
                "Please try again or contact support if the issue persists."
            )

    @app.on_message(filters.command("mirror"))
    async def mirror_command(client, message: Message):
        """Enhanced mirror command - download and upload to Telegram"""
        try:
            user_id = message.from_user.id
            
            # Check for active operations
            if leech_engine.get_user_download(user_id) or mirror_engine.get_user_upload(user_id):
                await message.reply_text(
                    "⚠️ **Operation Already Active**\n\n"
                    "You have an active download or upload.\n"
                    "Use `/cancel` to cancel or wait for completion."
                )
                return
            
            if len(message.command) < 2:
                await message.reply_text(
                    "❌ **Please provide a URL to mirror**\n\n"
                    "**Usage:** `/mirror [URL]`\n"
                    "**Examples:**\n"
                    "• `/mirror https://terabox.com/s/abc123`\n"
                    "• `/mirror https://youtube.com/watch?v=example`\n"
                    "• `/mirror https://example.com/file.zip`\n\n"
                    "🔗 **Supported:**\n"
                    "• All Terabox variants\n"
                    "• Direct HTTP/HTTPS links\n"
                    "• YouTube & 900+ sites\n"
                    "• Google Drive, Mega links\n\n"
                    "⚡ **Mirror = Download + Upload to Telegram**"
                )
                return
            
            url = " ".join(message.command[1:])
            
            if not validators.url(url):
                await message.reply_text(
                    "❌ **Invalid URL Format**\n\n"
                    "Please provide a valid URL.\n"
                    "**Example:** `https://terabox.com/s/abc123`"
                )
                return
            
            # Update user activity
            if db.enabled:
                await db.update_user_activity(user_id)
            
            status_msg = await message.reply_text("🚀 **Mirror Process Started!**")
            
            # Step 1: Download
            await status_msg.edit_text("📥 **Step 1/2: Downloading file...**")
            
            async def download_progress(downloaded, total, speed):
                try:
                    if total > 0:
                        progress = (downloaded / total) * 100
                        await status_msg.edit_text(
                            f"📥 **Step 1/2: Downloading...**\n\n"
                            f"📊 **Progress:** {progress:.1f}%\n"
                            f"⬇️ **Downloaded:** {get_readable_file_size(downloaded)}\n"
                            f"📦 **Total:** {get_readable_file_size(total)}\n"
                            f"⚡ **Speed:** {get_readable_file_size(speed)}/s"
                        )
                except:
                    pass
            
            leech_result = await leech_engine.leech_file(message, url, progress_callback=download_progress)
            
            if not leech_result['success']:
                await status_msg.edit_text(
                    f"❌ **Download Failed**\n\n"
                    f"**Error:** {leech_result['error']}\n\n"
                    f"Mirror process aborted."
                )
                return
            
            # Step 2: Upload
            await status_msg.edit_text("📤 **Step 2/2: Uploading to Telegram...**")
            
            caption = f"📁 **{leech_result['filename']}**\n📊 **Size:** {get_readable_file_size(leech_result['size'])}\n🔗 **Source:** {url[:50]}{'...' if len(url) > 50 else ''}"
            
            async def upload_progress(uploaded, total, speed):
                try:
                    if total > 0:
                        progress = (uploaded / total) * 100
                        await status_msg.edit_text(
                            f"📤 **Step 2/2: Uploading...**\n\n"
                            f"📁 **File:** {leech_result['filename'][:30]}{'...' if len(leech_result['filename']) > 30 else ''}\n"
                            f"📊 **Progress:** {progress:.1f}%\n"
                            f"⬆️ **Uploaded:** {get_readable_file_size(uploaded)}\n"
                            f"📦 **Total:** {get_readable_file_size(total)}\n"
                            f"⚡ **Speed:** {get_readable_file_size(speed)}/s"
                        )
                except:
                    pass
            
            mirror_result = await mirror_engine.mirror_to_telegram(
                client, message, leech_result['path'], caption, upload_progress
            )
            
            if mirror_result['success']:
                # Success
                files_count = len(mirror_result['files'])
                total_time = leech_result.get('download_time', 0) + mirror_result.get('upload_time', 0)
                
                success_text = f"""
✅ **Mirror Completed Successfully!**

📁 **Filename:** `{leech_result['filename']}`
📊 **Size:** {get_readable_file_size(leech_result['size'])}
📤 **Uploaded Files:** {files_count}
⏱️ **Total Time:** {total_time:.1f}s

🎉 **File(s) successfully mirrored to Telegram!**
                """
                
                if mirror_result.get('parts', 0) > 1:
                    success_text += f"\n📦 **Split into {mirror_result['parts']} parts** (file > 2GB)"
                
                await status_msg.edit_text(success_text)
                
            else:
                # Upload failed
                await status_msg.edit_text(
                    f"❌ **Upload Failed**\n\n"
                    f"**Download:** ✅ Success\n"
                    f"**Upload:** ❌ {mirror_result['error']}\n\n"
                    f"File downloaded successfully but upload to Telegram failed."
                )
            
            # Clean up downloaded file
            try:
                if os.path.exists(leech_result['path']):
                    os.remove(leech_result['path'])
            except:
                pass
                
        except Exception as e:
            logger.error(f"❌ Mirror command error: {e}")
            await message.reply_text("❌ An error occurred during the mirror process.")

    @app.on_message(filters.command("ytdl"))
    async def ytdl_command(client, message: Message):
        """YouTube-dl command for 900+ sites with format selection"""
        try:
            user_id = message.from_user.id
            
            if len(message.command) < 2:
                sites = universal_downloader.get_supported_sites()
                sites_text = "\n".join([f"• {site}" for site in sites[:15]])
                
                await message.reply_text(
                    f"❌ **Please provide a URL**\n\n"
                    f"**Usage:** `/ytdl [URL]`\n"
                    f"**Examples:**\n"
                    f"• `/ytdl https://youtube.com/watch?v=example`\n"
                    f"• `/ytdl https://instagram.com/p/example`\n"
                    f"• `/ytdl https://tiktok.com/@user/video/123`\n\n"
                    f"🌐 **Supported sites (900+):**\n{sites_text}\n• And many more...\n\n"
                    f"⚡ **Features:**\n"
                    f"• Auto quality selection\n"
                    f"• Multiple format options\n"
                    f"• Playlist support\n"
                    f"• Audio extraction"
                )
                return
            
            url = " ".join(message.command[1:])
            
            if not validators.url(url):
                await message.reply_text(
                    "❌ **Invalid URL**\n\n"
                    "Please provide a valid URL from supported platforms."
                )
                return
            
            status_msg = await message.reply_text("🔍 **Getting video information...**")
            
            # Get download info
            info = await universal_downloader.get_download_info(url)
            
            if not info['success']:
                await status_msg.edit_text(
                    f"❌ **Error:** {info['error']}\n\n"
                    f"**Possible causes:**\n"
                    f"• URL not supported\n"
                    f"• Private/restricted content\n"
                    f"• Geographic restrictions\n"
                    f"• Temporary server issues"
                )
                return
            
            # Show info with format options
            title = info['title'][:50] + ('...' if len(info['title']) > 50 else '')
            duration_text = f"{info.get('duration', 0)}s" if info.get('duration') else "Unknown"
            
            info_text = f"""
🎥 **{title}**

👤 **Uploader:** {info.get('uploader', 'Unknown')}
👀 **Views:** {info.get('view_count', 0):,}
⏱️ **Duration:** {duration_text}

📋 **Available Formats:**
            """
            
            keyboard = []
            formats = info.get('formats', [])[:5]  # Show top 5 formats
            
            for i, fmt in enumerate(formats):
                size_text = get_readable_file_size(fmt['filesize']) if fmt.get('filesize') else 'Unknown size'
                quality = fmt.get('quality', 'Unknown')
                ext = fmt.get('ext', 'mp4')
                
                button_text = f"{quality} ({ext}) - {size_text}"
                keyboard.append([InlineKeyboardButton(
                    button_text,
                    callback_data=f"ytdl_download_{user_id}_{i}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔄 Cancel", callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(info_text, reply_markup=reply_markup)
      
