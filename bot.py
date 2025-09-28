import asyncio
import logging
import re
from handlers.commands import setup_command_handlers
from handlers.callbacks import setup_callback_handlers
from handlers.messages import setup_message_handlers
from utils.bot_setup import create_bot, setup_logging, start_health_server
from utils.config import validate_environment

# NEW: Import verification handlers
from handlers.verification_handler import setup_verification_handlers

# Setup logging
logger = setup_logging()

# ✅ NEW: Universal URL Validator Function (FIXES "URL NOT SUPPORTED")
def is_terabox_url(url: str) -> bool:
    """Universal Terabox URL validator - SUPPORTS ALL DOMAINS"""
    try:
        url = url.strip().lower()
        
        # 🎯 ALL TERABOX DOMAIN PATTERNS (INCLUDING teraboxlink.com)
        terabox_patterns = [
            # Main domains
            r'terabox\.com',
            r'terasharelink\.com',
            r'teraboxlink\.com',      # ← THIS WAS THE MISSING PATTERN!
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
        
        # Check if URL contains any Terabox domain
        for pattern in terabox_patterns:
            if re.search(pattern, url):
                # Additional check for /s/ path (share URLs)
                if '/s/' in url or 'surl=' in url or '/file/' in url:
                    return True
        
        return False
        
    except Exception as e:
        logger.warning(f"URL validation error: {e}")
        return False

# ✅ NEW: Enhanced message handler setup
def setup_enhanced_message_handlers(app):
    """Setup enhanced message handlers with better URL validation"""
    from pyrogram import filters
    
    @app.on_message(filters.text & filters.private)
    async def handle_url_message(client, message):
        """Enhanced URL handler with better validation"""
        try:
            url = message.text.strip()
            
            # Skip if message is a command
            if url.startswith('/'):
                return
                
            # Check if it's a supported Terabox URL
            if is_terabox_url(url):
                logger.info(f"✅ Valid Terabox URL detected: {url[:50]}...")
                
                # Send to existing message handlers
                # This will trigger your existing download logic
                return
            else:
                # Check if it looks like a URL but isn't supported
                if any(check in url.lower() for check in ['http://', 'https://', 'www.', '.com', '.net', '.org']):
                    await message.reply(
                        "⚠️ **URL Not Supported**\n\n"
                        "**Supported domains:**\n"
                        "• terabox.com\n"
                        "• terasharelink.com\n" 
                        "• teraboxlink.com\n"  # ← NOW SHOWS AS SUPPORTED
                        "• nephobox.com\n"
                        "• 4funbox.com\n"
                        "• mirrobox.com\n"
                        "• And other Terabox variants\n\n"
                        "Please send a valid Terabox share link."
                    )
                    return
                    
        except Exception as e:
            logger.error(f"Enhanced message handler error: {e}")

    logger.info("✅ Enhanced message handlers setup complete")

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
        
        # ✅ ENHANCED: Setup message handlers with better URL validation
        try:
            setup_enhanced_message_handlers(app)
            logger.info("✅ Enhanced URL validation setup complete")
        except Exception as e:
            logger.warning(f"⚠️ Enhanced validation failed, using standard handlers: {e}")
            setup_message_handlers(app)
        
        # Setup your existing message handlers (as fallback/additional)
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
        
        # ✅ NEW: Enhanced status logging
        try:
            import os
            is_verify = os.environ.get("IS_VERIFY", "False")
            free_limit = os.environ.get("FREE_DOWNLOAD_LIMIT", "3")
            logger.info(f"🔐 Verification: {'ON' if is_verify.lower() == 'true' else 'OFF'}")
            logger.info(f"🎁 Free downloads: {free_limit} per user")
            
            # ✅ NEW: Log supported URL patterns
            logger.info("🌐 URL Support: terabox.com, terasharelink.com, teraboxlink.com, nephobox.com, etc.")
            
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

# ✅ NEW: Additional utility functions
def log_url_attempt(url: str):
    """Log URL validation attempts for debugging"""
    try:
        domain = url.split('//')[1].split('/')[0] if '//' in url else url.split('/')[0]
        logger.info(f"🔍 URL validation attempt: {domain}")
    except:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
    
