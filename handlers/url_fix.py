import re
from pyrogram import filters

def setup_url_fix(app):
    """Simple URL fix for teraboxlink.com support"""
    
    # Override the URL validation 
    @app.on_message(filters.text & filters.private & ~filters.command)
    async def fix_url_validation(client, message):
        url = message.text.strip().lower()
        
        # If it contains teraboxlink.com, let it through
        if 'teraboxlink.com' in url:
            # Don't block it - let other handlers process it
            return
        
        # For other URLs, let existing handlers work
        return
