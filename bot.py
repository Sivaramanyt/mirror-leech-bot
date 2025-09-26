from pyrogram import Client, filters
import os
import asyncio
from aiohttp import web

# Bot setup - using YOUR variable names
bot = Client(
    "mirror_pro_bot",
    api_id=int(os.environ.get("TELEGRAM_API", "29542645")),
    api_hash=os.environ.get("TELEGRAM_HASH", "06e505b8418565356ae79365df5d69e0"),
    bot_token=os.environ.get("BOT_TOKEN", "8382640536:AAE28ACIbdzFYO1cgJSs0BIAIfxg5Yv4vwo")
)

# Health server for Koyeb
async def health(request):
    return web.json_response({"status": "ok"})

async def start_server():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", "8080")))
    await site.start()
    print("✅ Health server started")

# Bot handlers
@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        f"🎉 **MIRROR PRO BOT IS WORKING!**\n\n"
        f"Hello {message.from_user.first_name}!\n\n"
        f"✅ Bot responding perfectly!\n"
        f"✅ Using correct Koyeb variables!\n"
        f"✅ TELEGRAM_API and TELEGRAM_HASH working!\n\n"
        f"Commands:\n"
        f"• /ping - Test response\n"
        f"• /help - Get help\n\n"
        f"🚀 **SUCCESS!**"
    )

@bot.on_message(filters.command("ping"))
async def ping_handler(client, message):
    await message.reply_text("🏓 **PONG!** Mirror Pro Bot is alive! ⚡")

@bot.on_message(filters.command("help"))
async def help_handler(client, message):
    await message.reply_text(
        "📋 **MIRROR PRO BOT HELP**\n\n"
        "Available Commands:\n"
        "• /start - Start the bot\n"
        "• /ping - Test bot response\n"
        "• /help - Show this help\n\n"
        "🚀 Bot is working perfectly!"
    )

# Run everything
async def main():
    await start_server()
    
    await bot.start()
    me = await bot.get_me()
    print(f"✅ Bot started: @{me.username}")
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
