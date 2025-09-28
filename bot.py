import os
import asyncio
from aiohttp import web

print("🚀 STARTING ENVIRONMENT DIAGNOSTIC...")

# Show ALL environment variables
print("🌍 ALL ENVIRONMENT VARIABLES FOUND:")
for key, value in sorted(os.environ.items()):
    # Mask sensitive data
    if any(sensitive in key.upper() for sensitive in ['TOKEN', 'KEY', 'SECRET', 'HASH']):
        masked_value = f"{value[:5]}***{value[-5:]}" if len(value) > 10 else "***"
    else:
        masked_value = value[:50] + "..." if len(value) > 50 else value
    print(f"  {key} = {masked_value}")

# Check for bot variables specifically
bot_vars = {
    'BOT_TOKEN': os.environ.get('BOT_TOKEN'),
    'API_ID': os.environ.get('API_ID'), 
    'API_HASH': os.environ.get('API_HASH'),
    'TELEGRAM_BOT_TOKEN': os.environ.get('TELEGRAM_BOT_TOKEN'),
    'TELEGRAM_API_ID': os.environ.get('TELEGRAM_API_ID'),
    'TELEGRAM_API_HASH': os.environ.get('TELEGRAM_API_HASH')
}

print("\n🔍 BOT-SPECIFIC VARIABLES:")
for name, value in bot_vars.items():
    status = "✅ FOUND" if value else "❌ MISSING"
    print(f"  {name}: {status}")

# Health server
async def health_check(request):
    found_count = sum(1 for v in bot_vars.values() if v)
    return web.Response(
        text=f"Environment Check: {found_count}/6 bot variables found\nAdd BOT_TOKEN, API_ID, API_HASH to Koyeb environment",
        status=200
    )

async def main():
    print("\n🌐 Starting health server...")
    
    app = web.Application()
    app.router.add_get('/', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"✅ Health server running on port {port}")
    
    if not any(bot_vars.values()):
        print("\n⚠️  NO BOT VARIABLES FOUND!")
        print("📋 ADD THESE IN KOYEB ENVIRONMENT:")
        print("   BOT_TOKEN = your_bot_token_from_botfather")
        print("   API_ID = your_api_id_from_my_telegram_org")
        print("   API_HASH = your_api_hash_from_my_telegram_org")
        print("\nThen redeploy the app.")
    
    # Keep running
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        print("⏰ Still waiting for environment variables...")

if __name__ == "__main__":
    asyncio.run(main())
    
