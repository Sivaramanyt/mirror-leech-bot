#!/usr/bin/env python3

"""
Mirror Leech Telegram Bot
Simplified version with core features for Koyeb deployment
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

# Import configuration and modules
import config
from utils.database import Database
from utils.helpers import get_readable_file_size, get_progress_bar_string
from modules.mirror import MirrorHandler
from modules.leech import LeechHandler
from modules.status import StatusHandler
from modules.auth import AuthHandler
from modules.gdrive import GDriveHandler
from utils.health_check import HealthCheckServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MirrorLeechBot:
    def __init__(self):
        self.client = None
        self.database = None
        self.mirror_handler = None
        self.leech_handler = None
        self.status_handler = None
        self.auth_handler = None
        self.gdrive_handler = None
        self.health_server = None
        
        # Task management
        self.active_tasks = {}
        self.task_counter = 0
        
    async def start_bot(self):
        """Initialize and start the bot"""
        try:
            # Validate configuration
            config.validate_config()
            
            # Initialize Pyrogram client
            self.client = Client(
                "mirror_leech_bot",
                api_id=config.TELEGRAM_API,
                api_hash=config.TELEGRAM_HASH,
                bot_token=config.BOT_TOKEN,
                workers=8,
                parse_mode=ParseMode.HTML
            )
            
            # Initialize database
            if config.DATABASE_URL:
                self.database = Database(config.DATABASE_URL)
                await self.database.connect()
                logger.info("✅ Database connected")
            
            # Initialize handlers
            self.mirror_handler = MirrorHandler(self)
            self.leech_handler = LeechHandler(self)
            self.status_handler = StatusHandler(self)
            self.auth_handler = AuthHandler(self)
            
            if config.GDRIVE_ID:
                self.gdrive_handler = GDriveHandler(self)
                logger.info("✅ Google Drive handler initialized")
            
            # Start health check server
            self.health_server = HealthCheckServer(config.PORT)
            await self.health_server.start()
            logger.info(f"✅ Health check server started on port {config.PORT}")
            
            # Register handlers
            await self.register_handlers()
            
            # Start the client
            await self.client.start()
            bot_info = await self.client.get_me()
            logger.info(f"✅ Bot started: @{bot_info.username}")
            
            # Send startup message to owner
            if config.OWNER_ID:
                try:
                    await self.client.send_message(
                        config.OWNER_ID,
                        "🤖 <b>Mirror Leech Bot Started!</b>\n\n"
                        f"<b>Bot:</b> @{bot_info.username}\n"
                        f"<b>Version:</b> 1.0\n"
                        f"<b>Database:</b> {'✅ Connected' if self.database else '❌ Not configured'}\n"
                        f"<b>GDrive:</b> {'✅ Enabled' if self.gdrive_handler else '❌ Not configured'}",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    logger.error(f"Failed to send startup message: {e}")
            
            # Keep the bot running
            await idle()
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            sys.exit(1)
    
    async def register_handlers(self):
        """Register all command and callback handlers - NO AUTH FILTER"""
        
        # Command handlers
        commands = [
            ("start", self.start_command),
            ("help", self.help_command),
            ("mirror", self.mirror_handler.mirror_command),
            ("leech", self.leech_handler.leech_command),
            ("ytdl", self.mirror_handler.ytdl_command),
            ("status", self.status_handler.status_command),
            ("cancel", self.cancel_command),
            ("cancelall", self.cancel_all_command),
            ("auth", self.auth_handler.auth_command),
            ("unauth", self.auth_handler.unauth_command),
            ("users", self.auth_handler.users_command),
            ("ping", self.ping_command),
            ("restart", self.restart_command),
            ("log", self.log_command),
        ]
        
        # Register handlers WITHOUT auth filter
        for cmd, handler in commands:
            cmd_with_suffix = f"{cmd}{config.CMD_SUFFIX}" if config.CMD_SUFFIX else cmd
            self.client.add_handler(
                MessageHandler(handler, filters.command(cmd_with_suffix))
            )
        
        # Callback query handler
        self.client.add_handler(CallbackQueryHandler(self.callback_handler))
        
        logger.info("✅ All handlers registered")
    
    def is_authorized(self, user_id: int, chat_id: int = None) -> bool:
        """Check if user is authorized - Simple version"""
        # Owner is always authorized
        if user_id == config.OWNER_ID:
            return True
        
        # Check sudo users
        if user_id in config.SUDO_USERS_LIST:
            return True
        
        # Check authorized chats
        if config.AUTHORIZED_CHATS_LIST and chat_id:
            return chat_id in config.AUTHORIZED_CHATS_LIST
        
        # If no restrictions set, allow all
        if not config.AUTHORIZED_CHATS_LIST and not config.SUDO_USERS_LIST:
            return True
        
        return False
    
    async def start_command(self, client: Client, message: Message):
        """Handle /start command"""
        await message.reply_text(
            "🤖 <b>Mirror Leech Bot</b>\n\n"
            "I can help you download and upload files from various sources!\n\n"
            "<b>Available Commands:</b>\n"
            "• <code>/mirror [link]</code> - Mirror to Google Drive\n"
            "• <code>/leech [link]</code> - Upload to Telegram\n"
            "• <code>/ytdl [link]</code> - Download from YouTube/social media\n"
            "• <code>/status</code> - Check active downloads\n"
            "• <code>/cancel [gid]</code> - Cancel a download\n"
            "• <code>/help</code> - Show detailed help\n\n"
            "Send <code>/help</code> for more information!",
            parse_mode=ParseMode.HTML
        )
    
    async def help_command(self, client: Client, message: Message):
        """Handle /help command"""
        help_text = """
🤖 <b>Mirror Leech Bot - Help</b>

<b>📥 Download Commands:</b>
• <code>/mirror [link]</code> - Download and upload to Google Drive
• <code>/leech [link]</code> - Download and upload to Telegram
• <code>/ytdl [link]</code> - Download from YouTube and 900+ sites

<b>📊 Management Commands:</b>
• <code>/status</code> - Show active downloads
• <code>/cancel [gid]</code> - Cancel a specific download
• <code>/cancelall</code> - Cancel all downloads
• <code>/ping</code> - Check bot response time

<b>🔧 Admin Commands:</b>
• <code>/auth [user_id]</code> - Authorize a user
• <code>/unauth [user_id]</code> - Remove authorization
• <code>/users</code> - List authorized users
• <code>/log</code> - Get bot logs
• <code>/restart</code> - Restart the bot

<b>📁 Supported Links:</b>
• Direct HTTP/HTTPS links
• Terabox (videos/folders)
• YouTube & 900+ sites via yt-dlp
• Google Drive links
• Mega links
• MediaFire links
• Torrent files & magnet links
• Telegram files

<b>💡 Usage Examples:</b>
<code>/mirror https://example.com/file.zip</code>
<code>/leech https://terabox.com/s/xxxxx</code>
<code>/ytdl https://youtube.com/watch?v=xxxxx</code>

<b>⚙️ Features:</b>
• Progress tracking with live updates
• Queue system for multiple downloads
• File size limits (2GB for free tier)
• Custom upload destinations
• Automatic file splitting for large files
        """
        await message.reply_text(help_text, parse_mode=ParseMode.HTML)
    
    async def cancel_command(self, client: Client, message: Message):
        """Handle /cancel command"""
        args = message.text.split()
        
        if len(args) < 2:
            # Show cancellable tasks
            if not self.active_tasks:
                await message.reply_text("❌ No active downloads to cancel")
                return
            
            buttons = []
            for gid, task_info in self.active_tasks.items():
                buttons.append([
                    InlineKeyboardButton(
                        f"❌ {task_info.get('name', 'Unknown')[:20]}...", 
                        callback_data=f"cancel_{gid}"
                    )
                ])
            
            await message.reply_text(
                "📋 <b>Select download to cancel:</b>",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            gid = args[1]
            if gid in self.active_tasks:
                # Cancel specific task
                task_info = self.active_tasks.pop(gid)
                await message.reply_text(f"✅ Cancelled: {task_info.get('name', 'Unknown')}")
            else:
                await message.reply_text("❌ Invalid download ID")
    
    async def cancel_all_command(self, client: Client, message: Message):
        """Handle /cancelall command"""
        if not self.active_tasks:
            await message.reply_text("❌ No active downloads to cancel")
            return
        
        count = len(self.active_tasks)
        self.active_tasks.clear()
        await message.reply_text(f"✅ Cancelled {count} download(s)")
    
    async def ping_command(self, client: Client, message: Message):
        """Handle /ping command"""
        import time
        start_time = time.time()
        ping_msg = await message.reply_text("🏓 Pong!")
        end_time = time.time()
        
        response_time = round((end_time - start_time) * 1000, 2)
        await ping_msg.edit_text(f"🏓 <b>Pong!</b>\n<b>Response time:</b> {response_time}ms", parse_mode=ParseMode.HTML)
    
    async def restart_command(self, client: Client, message: Message):
        """Handle /restart command"""
        if message.from_user.id != config.OWNER_ID:
            await message.reply_text("❌ Only owner can restart the bot")
            return
        
        await message.reply_text("🔄 Restarting bot...")
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    async def log_command(self, client: Client, message: Message):
        """Handle /log command"""
        if message.from_user.id not in config.SUDO_USERS_LIST:
            await message.reply_text("❌ You don't have permission to view logs")
            return
        
        try:
            if os.path.exists("bot.log"):
                await message.reply_document("bot.log", caption="📄 Bot Logs")
            else:
                await message.reply_text("❌ Log file not found")
        except Exception as e:
            await message.reply_text(f"❌ Failed to send logs: {str(e)}")
    
    async def callback_handler(self, client: Client, callback_query: CallbackQuery):
        """Handle callback queries"""
        data = callback_query.data
        
        if data.startswith("cancel_"):
            gid = data.replace("cancel_", "")
            if gid in self.active_tasks:
                task_info = self.active_tasks.pop(gid)
                await callback_query.message.edit_text(
                    f"✅ <b>Cancelled:</b> {task_info.get('name', 'Unknown')}",
                    parse_mode=ParseMode.HTML
                )
            else:
                await callback_query.answer("❌ Download not found", show_alert=True)
        
        await callback_query.answer()
    
    def generate_task_id(self) -> str:
        """Generate unique task ID"""
        self.task_counter += 1
        return f"task_{self.task_counter}"
    
    async def stop_bot(self):
        """Cleanup and stop the bot"""
        logger.info("🔄 Stopping bot...")
        
        if self.health_server:
            await self.health_server.stop()
        
        if self.database:
            await self.database.close()
        
        if self.client:
            await self.client.stop()
        
        logger.info("✅ Bot stopped")

# Global bot instance
bot = MirrorLeechBot()

async def main():
    """Main function to run the bot"""
    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("🔄 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        await bot.stop_bot()

if __name__ == "__main__":
    asyncio.run(main())
            
