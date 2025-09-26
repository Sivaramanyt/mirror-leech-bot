import os
import asyncio
import logging
from pyrogram import Client, filters
from aiohttp import web

# MAXIMUM logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Config
API_ID = int(os.environ.get("API_ID") or os.environ.get("TELEGRAM_API", "0"))
API_HASH = os.environ.get("API_HASH") or os.environ.get("TELEGRAM_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

logger.info(f"🔧 FULL CONFIG - API_ID: {API_ID}, API_HASH: {API_HASH[:10]}..., Token: {BOT_TOKEN}")

# Health check
async def health_check(request):
    return web.json_response({"status": "healthy", "debug": "active"})

async def start_health_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", "8080")))
    await site.start()
    logger.info("✅ Health server started")

# Bot
app = Client("debug_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# CATCH EVERYTHING
@app.on_message()
async def catch_all_messages(client, message):
    logger.info(f"🔥🔥🔥 INCOMING MESSAGE DETECTED!")
    logger.info(f"🔥🔥🔥 Text: {message.text}")
    logger.info(f"🔥🔥🔥 From: {message.from_user.id} (@{message.from_user.username})")
    logger.info(f"🔥🔥🔥 Chat: {message.chat.id}")
    logger.info(f"🔥🔥🔥 Date: {message.date}")
    
    try:
        response = f"🎉 MESSAGE RECEIVED!\n\nYou sent: {message.text}\nYour ID: {message.from_user.id}\nBot is ALIVE!"
        await message.reply_text(response)
        logger.info("🔥🔥🔥 RESPONSE SENT SUCCESSFULLY!")
    except Exception as e:
        logger.error(f"❌ Response error: {e}")

# SPECIFIC HANDLER FOR /start
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    logger.info(f"🚀🚀🚀 START COMMAND DETECTED!")
    await message.reply_text("🎉 START COMMAND WORKS!")

async def main():
    try:
        logger.info("🚀 Starting NUCLEAR DEBUG bot...")
        
        await start_health_server()
        
        await app.start()
        me = await app.get_me()
        logger.info(f"🤖 BOT INFO: @{me.username} (ID: {me.id})")
        logger.info(f"🤖 BOT NAME: {me.first_name}")
        logger.info(f"🤖 BOT IS_BOT: {me.is_bot}")
        
        logger.info("🔥🔥🔥 SEND ANY MESSAGE TO TEST!")
        logger.info("🔥🔥🔥 BOT IS READY TO RECEIVE MESSAGES!")
        
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
    
