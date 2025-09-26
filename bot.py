from pyrogram import Client, filters
import os
import asyncio
from aiohttp import web
import signal
import sys

# Bot setup
bot = Client(
    "mirror_pro_bot",
    api_id=int(os.environ.get("TELEGRAM_API", "29542645")),
    api_hash=os.environ.get("TELEGRAM_HASH", "06e505b8418565356ae79365df5d69e0"),
    bot_token=os.environ.get("BOT_TOKEN", "8382640536:AAE28ACIbdzFYO1cgJSs0BIAIfxg5Yv4vwo")
)

# Global event to keep running
running = asyncio.Event()

# Health server
async def health(request):
    return web.json_response({"status": "ok", "bot": "alive"})

async def start_server():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", "8080")))
    await site.start()
    print("✅ Health server started on port 8080")

# Handlers
@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    print(f"🔥 START command received from {message.from_user.id}")
    await message.reply_text(
        f"🎉 **MIRROR PRO BOT IS ALIVE!**\n\n"
        f"Hello {message.from_user.first_name}!\n\n"
        f"✅ Bot responding perfectly!\n"
        f"✅ Handlers working!\n"
        f"✅ Pyrogram connected!\n\n"
        f"Commands:\n"
        f"• /ping - Test response\n"
        f"• /status - Bot status\n\n"
        f"🚀 **FINALLY WORKING!**"
    )
    print("✅ START response sent successfully")

@bot.on_message(filters.command("ping"))
async def ping_handler(client, message):
    print(f"🏓 PING received from {message.from_user.id}")
    await message.reply_text("🏓 **PONG!** Bot is fully operational! ⚡")

@bot.on_message()
async def all_messages(client, message):
    print(f"📨 Message: '{message.text}' from {message.from_user.id}")

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print("🛑 Received shutdown signal")
    running.set()

# Main function
async def main():
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print("🚀 Starting Mirror Pro Bot...")
        
        # Start health server
        await start_server()
        
        # Start bot
        print("📡 Connecting to Telegram...")
        await bot.start()
        
        # Get bot info
        me = await bot.get_me()
        print(f"✅ Bot started: @{me.username} (ID: {me.id})")
        print(f"🎯 Bot name: {me.first_name}")
        print("🔥 Bot is ready to receive messages!")
        
        # Keep running until signal
        await running.wait()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🛑 Stopping bot...")
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    
