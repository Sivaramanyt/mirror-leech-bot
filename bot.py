import asyncio
import logging

from handlers.commands import setup_command_handlers
from handlers.callbacks import setup_callback_handlers
from handlers.messages import setup_message_handlers
from utils.bot_setup import create_bot, setup_logging, start_health_server
from utils.config import validate_environment

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
        
        # Setup handlers
        setup_command_handlers(app)
        setup_callback_handlers(app)
        setup_message_handlers(app)
        
        # Start bot
        await app.start()
        me = await app.get_me()
        logger.info(f"🤖 Bot started: @{me.username} (ID: {me.id})")
        logger.info("🎯 Bot is ready for Terabox downloads!")
        
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
