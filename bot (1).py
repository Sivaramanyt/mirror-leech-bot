import asyncio
import logging

from handlers.commands import setup_command_handlers
from handlers.callbacks import setup_callback_handlers
from handlers.messages import setup_message_handlers
from utils.bot_setup import create_bot, setup_logging, start_health_server
from utils.config import validate_environment

# NEW: Import verification handlers
from handlers.verification_handler import setup_verification_handlers

# Setup logging
logger = setup_logging()

async def main():
    """Main bot entry point"""
    try:
        logger.info("🚀 Starting Terabox Leech Bot...")
        
        # Validate environment
        if not validate_environment():
            logger.error("❌ Environment validation failed")
            return
        
        # Create bot instance
        app = create_bot()
        
        # Start health server
        await start_health_server()
        
        # Setup handlers (YOUR EXISTING HANDLERS)
        setup_command_handlers(app)
        setup_callback_handlers(app)
        setup_message_handlers(app)
        
        # NEW: Setup verification handlers
        try:
            setup_verification_handlers(app)
            logger.info("✅ Verification handlers setup complete")
        except ImportError:
            logger.warning("⚠️ Verification system not available (optional)")
        except Exception as e:
            logger.error(f"❌ Verification setup failed: {e}")
            logger.info("🔄 Continuing without verification system...")
        
        # Start bot
        await app.start()
        
        me = await app.get_me()
        logger.info(f"🤖 Bot started: @{me.username} (ID: {me.id})")
        logger.info("🎯 Bot is ready for Terabox downloads!")
        
        # NEW: Log verification status
        try:
            import os
            is_verify = os.environ.get("IS_VERIFY", "False")
            free_limit = os.environ.get("FREE_DOWNLOAD_LIMIT", "3")
            logger.info(f"🔐 Verification: {'ON' if is_verify.lower() == 'true' else 'OFF'}")
            logger.info(f"🎁 Free downloads: {free_limit} per user")
        except:
            pass
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        try:
            await app.stop()
        except:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        
