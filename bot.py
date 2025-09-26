import os
import asyncio
from pyrogram import Client, filters
from aiohttp import web

# Environment variables
bot = Client(
    "simple_bot",
    api_id=int(os.environ.get("API_ID", "0")),
    api_hash=os.environ.get("API_HASH", ""),
    bot_token=os.environ.get("BOT_TOKEN", "")
)

# Health check
async def health(request):
    return web.json_response({"ok": True})

async def start_server():
    app = web.Application()
    app.router.add_get('/', health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", "8080")))
    await site.start()

# Handlers
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("🎉 **BOT IS WORKING!** Send /ping to test!")

@bot.on_message(filters.command("ping"))
async def ping_cmd(client, message):
    await message.reply("🏓 **PONG!** Bot is alive!")

@bot.on_message()
async def echo_all(client, message):
    if message.text and not message.text.startswith('/'):
        await message.reply(f"✅ I received: {message.text}")

# Main
async def main():
    await start_server()
    print("✅ Health server started")
    async with bot:
        print("🤖 Bot started!")
        await asyncio.Event().wait()   # keeps running

if __name__ == "__main__":
    asyncio.run(main())
    
