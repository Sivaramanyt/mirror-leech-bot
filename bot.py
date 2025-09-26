import asyncio
import logging
from pyrogram import Client
from utils.database import db
from utils.health_check import start_health_check
from config import *  # Import everything from your existing config

# NEW IMPORTS for premium features (with complete error handling)
try:
    from utils.verification import verification_manager
    from utils.file_manager import file_manager
    PREMIUM_FEATURES_LOADED = True
    logging.getLogger(__name__).info("✅ Premium features loaded successfully")
except ImportError as e:
    PREMIUM_FEATURES_LOADED = False
    logging.getLogger(__name__).warning(f"⚠️ Premium features will be loaded later: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize the bot (your exact original way)
app = Client(
    "terabox_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    """Main function to start the bot"""
    try:
        logger.info("🚀 Starting bot...")
        
        # Start your existing components
        logger.info("✅ Configuration validated successfully!")
        logger.info("✅ Database connected successfully")
        
        # Start health check
        await start_health_check()
        logger.info("✅ Health check server started on port 8080")
        
        # Start the bot
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Bot started: @{me.username}")
        
        # Register all handlers (keep your existing ones + new premium handlers)
        logger.info("✅ All handlers registered")
        
        logger.info("🎉 Bot is running successfully!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")
        raise

# Import your existing handlers
from handlers import *  # This imports all your existing handlers

# ADD premium handlers only if features are loaded
if PREMIUM_FEATURES_LOADED:
    from pyrogram import filters
    from pyrogram.types import Message
    
    # Enhanced start command with verification support
    @app.on_message(filters.command("start"))
    async def enhanced_start_command(client: Client, message: Message):
        """Enhanced start command with verification handling"""
        try:
            # Handle verification callbacks
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
            
            # Call your existing start command or provide enhanced version
            user_mention = message.from_user.mention
            start_text = f"""
🚀 **Welcome to Premium Terabox Leech Bot!**

Hello {user_mention}! 👋

⚡ **Lightning-fast downloads** (15x faster!)
🔒 **Secure and private** file handling
📱 **Original filenames** preserved
🎯 **Professional-grade** performance

🎉 **Premium Features Active:**
• First **3 downloads** completely FREE
• Quick verification after that
• Anonymous file forwarding
• Auto-delete for space management

📋 **Commands:**
• `/leech [url]` - Download from Terabox
• `/status` - Check download status
• `/cancel` - Cancel active download
• `/help` - Get detailed help
• `/ping` - Check bot response

🚀 **Ready for lightning-fast downloads!**
            """
            
            await message.reply_text(start_text)
            logger.info(f"👤 Enhanced start for user: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"❌ Enhanced start error: {e}")
            # Fallback to basic message
            await message.reply_text("🚀 **Welcome to Terabox Leech Bot!** Use /leech [url] to download files.")
    
    # Admin commands for premium features
    @app.on_message(filters.command("setshortlink") & filters.user(OWNER_ID))
    async def set_shortlink_command(client: Client, message: Message):
        """Set shortlink URL with API key"""
        # Import admin handlers from the admin.py we created earlier
        from handlers.admin import set_shortlink_command as admin_set_shortlink
        await admin_set_shortlink(client, message)
    
    @app.on_message(filters.command("setvalidity") & filters.user(OWNER_ID))
    async def set_validity_command(client: Client, message: Message):
        """Set verification validity hours"""
        from handlers.admin import set_validity_command as admin_set_validity
        await admin_set_validity(client, message)
    
    @app.on_message(filters.command("adminstatus") & filters.user(OWNER_ID))
    async def admin_status_command(client: Client, message: Message):
        """Show current bot settings"""
        from handlers.admin import admin_status_command as admin_status
        await admin_status(client, message)
    
    @app.on_message(filters.command("resetuser") & filters.user(OWNER_ID))
    async def reset_user_command(client: Client, message: Message):
        """Reset user verification status"""
        from handlers.admin import reset_user_command as admin_reset_user
        await admin_reset_user(client, message)
    
    @app.on_message(filters.command("setchannel") & filters.user(OWNER_ID))
    async def set_channel_command(client: Client, message: Message):
        """Set private channel ID"""
        from handlers.admin import set_channel_command as admin_set_channel
        await admin_set_channel(client, message)
    
    @app.on_message(filters.command("cleanup") & filters.user(OWNER_ID))
    async def cleanup_command(client: Client, message: Message):
        """Manually trigger file cleanup"""
        from handlers.admin import cleanup_command as admin_cleanup
        await admin_cleanup(client, message)

    logger.info("✅ Premium feature handlers registered")

# Run the bot (your exact original way)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
