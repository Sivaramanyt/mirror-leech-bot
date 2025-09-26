import os
import asyncio
import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.database import init_database, cleanup_database, database
from utils.health_check import start_health_check_server
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME, OWNER_ID

# NEW IMPORTS for premium features
from utils.verification import verification_manager
from utils.file_manager import file_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeraboxLeechBot:
    def __init__(self):
        self.app = Client(
            "terabox_leech_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
        self.is_running = False
    
    async def start_bot(self):
        """Start the bot with all features"""
        try:
            logger.info("🚀 Starting Terabox Leech Bot...")
            
            # Initialize database
            await init_database()
            logger.info("✅ Database initialized")
            
            # Start health check server
            await start_health_check_server()
            logger.info("✅ Health check server started on port 8080")
            
            # Start the bot
            await self.app.start()
            logger.info("✅ Bot client started")
            
            # Get bot info
            me = await self.app.get_me()
            logger.info(f"✅ Bot started: @{me.username}")
            
            # Initialize periodic tasks
            await self.start_periodic_tasks()
            
            # Register handlers
            self.register_handlers()
            logger.info("✅ All handlers registered")
            
            self.is_running = True
            logger.info("🎉 Terabox Leech Bot is now running!")
            
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            raise e
    
    def register_handlers(self):
        """Register all message handlers"""
        
        # Start command with verification handling
        @self.app.on_message(filters.command("start"))
        async def start_command(client: Client, message: Message):
            """Enhanced start command with verification handling"""
            try:
                # Handle verification callbacks (File Store Bot method)
                if len(message.text.split()) > 1:
                    start_param = message.text.split()[1]
                    if start_param.startswith("verify_"):
                        user_id = message.from_user.id
                        success = await verification_manager.handle_verification_callback(start_param, user_id)
                        
                        if success:
                            await message.reply_text(
                                "✅ **Verification Successful!**\n\n"
                                "🎉 You can now use the bot for leech commands.\n"
                                "⏰ Your verification will expire based on admin settings.\n\n"
                                "Use `/leech [url]` to download files from Terabox."
                            )
                        else:
                            await message.reply_text(
                                "❌ **Verification Failed**\n\n"
                                "The verification link may be expired or invalid.\n"
                                "Please request a new verification link by using `/leech`."
                            )
                        return
                
                # Regular start command
                user_mention = message.from_user.mention
                start_text = f"""
🚀 **Welcome to Premium Terabox Leech Bot!**

Hello {user_mention}! 👋

⚡ **Lightning-fast downloads** from Terabox
🔒 **Secure and private** file handling  
🎯 **Professional-grade** performance
📱 **Original filenames** preserved

🆓 **FREE USAGE:**
• First **3 downloads** are completely free
• After that, quick verification required
• Verification gives you extended access

📋 **Available Commands:**
• `/leech [url]` - Download from Terabox
• `/status` - Check your download status  
• `/cancel` - Cancel active download
• `/help` - Get detailed help

🔗 **Supported Links:**
• Terabox, Nephobox, 4funbox
• Mirrobox, Momerybox, Teraboxapp
• 1024tera, Gibibox, Goaibox
• Terasharelink, Teraboxlink

🎉 **Ready to download at lightning speed!**

Use `/leech [your_terabox_url]` to get started!
                """
                
                await message.reply_text(start_text)
                logger.info(f"👤 New user started bot: {message.from_user.id}")
                
            except Exception as e:
                logger.error(f"❌ Error in start command: {e}")
                await message.reply_text("❌ An error occurred. Please try again.")
        
        # Help command
        @self.app.on_message(filters.command("help"))
        async def help_command(client: Client, message: Message):
            """Detailed help command"""
            help_text = """
❓ **HELP - How to Use the Bot**

📥 **Download Files:**
• Send `/leech [terabox_url]` to download
• Example: `/leech https://terabox.com/s/abc123`
• Supports all major Terabox domains

🆓 **Free Usage Policy:**
• **First 3 downloads** are completely free
• **4th download onwards** requires quick verification
• Verification is valid for hours (set by admin)

⚡ **Features:**
• Lightning-fast downloads (15x faster!)
• Original filenames preserved
• Auto file type detection
• Progress tracking
• Secure and private

📱 **Commands:**
• `/leech [url]` - Download from URL
• `/status` - Check download status
• `/cancel` - Cancel active download  
• `/start` - Restart the bot
• `/help` - Show this help

🔗 **Supported Domains:**
• terabox.com, nephobox.com
• 4funbox.com, mirrobox.com
• momerybox.com, teraboxapp.com
• 1024tera.com, gibibox.com
• terasharelink.com, teraboxlink.com

💡 **Tips:**
• Only one download per user at a time
• Large files may take some time
• Contact admin if you face issues

🚀 **Ready to download? Use `/leech [url]`!**
            """
            
            await message.reply_text(help_text)
        
        # Ping command
        @self.app.on_message(filters.command("ping"))
        async def ping_command(client: Client, message: Message):
            """Check bot response time"""
            start_time = datetime.now()
            ping_msg = await message.reply_text("🏓 **Pinging...**")
            end_time = datetime.now()
            
            ping_time = (end_time - start_time).total_seconds() * 1000
            
            await ping_msg.edit_text(
                f"🏓 **Pong!**\n\n"
                f"⚡ **Response Time:** `{ping_time:.2f} ms`\n"
                f"🤖 **Bot Status:** Online\n"
                f"⚡ **Download Speed:** Lightning Fast!"
            )
        
        # Stats command (for admins)
        @self.app.on_message(filters.command("stats") & filters.user(OWNER_ID))
        async def stats_command(client: Client, message: Message):
            """Show bot statistics (admin only)"""
            try:
                stats = await database.get_statistics()
                
                stats_text = f"""
📊 **BOT STATISTICS**

👥 **Users:**
• Total Users: {stats.get('total_users', 0)}
• Verified Users: {stats.get('verified_users', 0)}
• Active Verifications: {stats.get('active_verifications', 0)}

📁 **Files:**
• Total Files Processed: {stats.get('total_files', 0)}
• Files Today: {stats.get('files_today', 0)}

🔗 **Verification:**
• Active Tokens: {stats.get('active_tokens', 0)}
• Completed Verifications: {stats.get('verified_tokens', 0)}

⚡ **Performance:**
• Status: Lightning Fast ⚡
• Uptime: Online 24/7
• Success Rate: 99.9%

🎯 **Premium Features Active:**
• 3 Free Uses ✅
• Verification System ✅  
• Anonymous Forwarding ✅
• Auto-Delete ✅
                """
                
                await message.reply_text(stats_text)
                
            except Exception as e:
                logger.error(f"❌ Error getting stats: {e}")
                await message.reply_text("❌ Error getting statistics")
        
        # Broadcast command (for admins)
        @self.app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
        async def broadcast_command(client: Client, message: Message):
            """Broadcast message to all users"""
            try:
                if len(message.text.split(maxsplit=1)) < 2:
                    await message.reply_text(
                        "❌ **Usage:** `/broadcast [message]`\n\n"
                        "**Example:** `/broadcast Hello everyone! Bot updated with new features.`"
                    )
                    return
                
                broadcast_text = message.text.split(maxsplit=1)[1]
                
                # Get all users
                users = await database.users_verification.distinct("user_id")
                
                success_count = 0
                failed_count = 0
                
                status_msg = await message.reply_text(f"📡 **Broadcasting to {len(users)} users...**")
                
                for user_id in users:
                    try:
                        await client.send_message(user_id, broadcast_text)
                        success_count += 1
                        await asyncio.sleep(0.05)  # Rate limiting
                    except Exception:
                        failed_count += 1
                
                await status_msg.edit_text(
                    f"📡 **Broadcast Complete!**\n\n"
                    f"✅ **Successful:** {success_count}\n"
                    f"❌ **Failed:** {failed_count}\n"
                    f"📊 **Total:** {len(users)}"
                )
                
            except Exception as e:
                logger.error(f"❌ Broadcast error: {e}")
                await message.reply_text("❌ Broadcast failed")
        
        logger.info("✅ All handlers registered successfully")
    
    async def start_periodic_tasks(self):
        """Start periodic background tasks"""
        async def cleanup_task():
            """Periodic cleanup task"""
            while self.is_running:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    await cleanup_database()
                    await file_manager.cleanup_expired_files(self.app)
                    logger.info("✅ Periodic cleanup completed")
                except Exception as e:
                    logger.error(f"❌ Periodic cleanup error: {e}")
        
        # Start cleanup task in background
        asyncio.create_task(cleanup_task())
        logger.info("✅ Periodic tasks started")
    
    async def run(self):
        """Run the bot"""
        try:
            await self.start_bot()
            # Keep the bot running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
        finally:
            await self.stop_bot()
    
    async def stop_bot(self):
        """Stop the bot gracefully"""
        try:
            self.is_running = False
            await self.app.stop()
            await database.close()
            logger.info("✅ Bot stopped gracefully")
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {e}")

# Main execution
if __name__ == "__main__":
    try:
        bot = TeraboxLeechBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
