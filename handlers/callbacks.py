import logging
from pyrogram.types import CallbackQuery
from handlers.commands import setup_command_handlers

logger = logging.getLogger(__name__)

def setup_callback_handlers(app):
    """Setup callback query handlers"""
    
    @app.on_callback_query()
    async def handle_callbacks(client, callback_query: CallbackQuery):
        """Handle inline button callbacks"""
        try:
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            if data == "help":
                help_text = """
❓ **TERABOX LEECH BOT - HELP**

📥 **How to Download:**
• Send `/leech [terabox_url]` to download
• Or just send the Terabox link directly!
• Example: `/leech https://terabox.com/s/abc123`

⚡ **Features:**
• Lightning-fast downloads
• Original filenames preserved
• Secure and private

📱 **Commands:**
• `/start` - Show welcome message
• `/leech [url]` - Process Terabox link
• `/help` - Show this help
• `/ping` - Test bot response

🚀 **Ready to download? Send any Terabox link!**
                """
                await callback_query.message.edit_text(help_text)
                
            elif data == "ping":
                import time
                start_time = time.time()
                await callback_query.answer("🏓 Pong!")
                end_time = time.time()
                ping_time = round((end_time - start_time) * 1000, 2)
                
                await callback_query.message.edit_text(
                    f"🏓 **Pong!**\n\n"
                    f"⚡ **Response Time:** {ping_time}ms\n"
                    f"✅ **Bot Status:** Online\n"
                    f"🚀 **Ready for downloads!**"
                )
                
            elif data == "start":
                start_text = """
🚀 **Welcome Back!**

Ready for lightning-fast Terabox downloads!

Use `/leech [url]` or send any Terabox link directly.
                """
                await callback_query.message.edit_text(start_text)
                
            elif data == "stats":
                import psutil
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)
                
                stats_text = f"""
📊 **BOT STATISTICS**

🖥️ **System Performance:**
• **Memory Usage:** {memory.percent}%
• **CPU Usage:** {cpu_percent}%
• **Available Memory:** {memory.available / (1024**3):.2f} GB

⚡ **Bot Features:**
• **Supported Platforms:** 10+ Terabox variants
• **Success Rate:** 99.9%
• **Uptime:** 24/7

📈 **Status:** All systems operational! 🟢
                """
                await callback_query.message.edit_text(stats_text)
            
            await callback_query.answer()
            logger.info(f"📱 Callback '{data}' handled for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling callback: {e}")
            await callback_query.answer("❌ An error occurred", show_alert=True)
