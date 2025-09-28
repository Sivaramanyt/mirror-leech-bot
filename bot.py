import logging
import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import threading
from aiohttp import web
import time
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ✅ Simple URL validator
def is_terabox_url(url: str) -> bool:
    """Simple URL validator"""
    try:
        url = url.lower()
        terabox_domains = [
            'terabox.com', 'terasharelink.com', 'teraboxlink.com',
            'nephobox.com', '4funbox.com', 'mirrobox.com',
            '1024tera.com', '1024terabox.com'
        ]
        
        for domain in terabox_domains:
            if domain in url and '/s/' in url:
                return True
        return False
    except:
        return False

# ✅ START command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    try:
        await update.message.reply_text(
            "🚀 **Terabox Simple Bot**\n\n"
            "**Commands:**\n"
            "• `/start` - Show this message\n"
            "• `/leech <url>` - Process Terabox URL\n\n"
            "**Supported domains:**\n"
            "• terabox.com ✅\n"
            "• terasharelink.com ✅\n"
            "• teraboxlink.com ✅\n"
            "• 1024terabox.com ✅\n"
            "• nephobox.com ✅\n"
            "• 4funbox.com ✅\n"
            "• mirrobox.com ✅\n\n"
            "**Usage:** `/leech https://terabox.com/s/xxxxx`",
            parse_mode='Markdown'
        )
        logger.info("✅ START command processed")
    except Exception as e:
        logger.error(f"START error: {e}")

# ✅ LEECH command - Simple version
async def leech_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple leech command"""
    try:
        user_id = update.effective_user.id
        logger.info(f"📨 LEECH command from user {user_id}")
        
        # Check URL
        if not context.args:
            await update.message.reply_text(
                "❌ **No URL provided**\n\n"
                "**Usage:** `/leech <terabox_url>`\n\n"
                "**Example:**\n"
                "`/leech https://terabox.com/s/xxxxx`",
                parse_mode='Markdown'
            )
            return
        
        url = ' '.join(context.args)
        logger.info(f"🔍 Processing URL: {url}")
        
        # Validate URL
        if not is_terabox_url(url):
            await update.message.reply_text(
                "⚠️ **Invalid Terabox URL**\n\n"
                "**Supported domains:**\n"
                "• terabox.com\n"
                "• terasharelink.com\n"
                "• teraboxlink.com ✅\n"
                "• 1024terabox.com ✅\n"
                "• nephobox.com\n"
                "• 4funbox.com\n"
                "• mirrobox.com",
                parse_mode='Markdown'
            )
            return
        
        # Process URL
        await update.message.reply_text(
            f"✅ **Valid Terabox URL Detected**\n\n"
            f"**URL:** `{url[:60]}...`\n\n"
            f"**Status:** URL validation successful\n"
            f"**Domain:** Recognized and supported\n\n"
            f"**Note:** This is a simple version that validates URLs.\n"
            f"For actual file downloads, Terabox has restrictions that\n"
            f"prevent direct downloading through bots.\n\n"
            f"**What this bot can do:**\n"
            f"✅ Validate Terabox URLs\n"
            f"✅ Recognize supported domains\n"
            f"✅ Parse URL structure\n\n"
            f"**Limitations:**\n"
            f"❌ Direct file downloads (Terabox restrictions)\n"
            f"❌ Bypass anti-bot protection\n"
            f"❌ Access private/password-protected files",
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ LEECH processed for user {user_id}")
        
    except Exception as e:
        logger.error(f"LEECH error: {e}")
        try:
            await update.message.reply_text(
                f"❌ **Error processing request**\n\n"
                f"Error: `{str(e)[:100]}`",
                parse_mode='Markdown'
            )
        except:
            pass

# ✅ URL handler for direct messages
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direct URL messages"""
    try:
        url = update.message.text.strip()
        
        if not any(x in url.lower() for x in ['http', 'terabox', '.com']):
            return
        
        if is_terabox_url(url):
            context.args = [url]
            await leech_command(update, context)
        else:
            await update.message.reply_text(
                "⚠️ **URL not supported**\n\n"
                "Please use: `/leech <terabox_url>`",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"URL handler error: {e}")

# ✅ Health server
def start_health_server():
    """Simple health server"""
    async def health_check(request):
        return web.Response(
            text="✅ Terabox Simple Bot Online\n🎯 Ready for URL validation",
            status=200
        )
    
    async def run_server():
        app = web.Application()
        app.router.add_get('/', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        port = int(os.environ.get('PORT', 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"✅ Health server started on port {port}")
        
        while True:
            await asyncio.sleep(1)
    
    def server_thread():
        asyncio.run(run_server())
    
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

def main():
    """Main function"""
    try:
        logger.info("🚀 Starting Simple Terabox Bot...")
        
        if not BOT_TOKEN:
            logger.error("❌ Missing BOT_TOKEN")
            return
            
        logger.info("✅ Environment validated")
        
        # Start health server
        start_health_server()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("leech", leech_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
        
        logger.info("✅ Simple bot ready")
        
        # Start polling
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
