import logging
from pyrogram import filters
from pyrogram.types import Message

logger = logging.getLogger(__name__)

def setup_verification_handlers(app):
    """Setup verification handlers"""
    
    @app.on_message(filters.command("verify") & filters.private)
    async def verify_command(client, message: Message):
        """Handle /verify token"""
        from utils.verification import verification
        
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **Usage:** `/verify [token]`\n"
                "**Example:** `/verify abc12345`"
            )
            return
        
        token = message.command[1]
        user_id = message.from_user.id
        
        result = await verification.verify_token(token, user_id)
        
        if result["success"]:
            await message.reply_text("✅ **Verification successful! Processing download...**")
            
            # Call your existing leech command
            from handlers.commands import leech_command
            fake_message = message
            fake_message.command = ["leech", result["url"]]
            fake_message.text = f"/leech {result['url']}"
            await leech_command(client, fake_message)
            
        else:
            await message.reply_text(f"❌ **Verification failed:** {result['error']}")

    @app.on_message(filters.command("mystats") & filters.private)
    async def stats_command(client, message: Message):
        """Show user stats"""
        from utils.verification import verification
        
        user_id = message.from_user.id
        downloads = await verification.get_user_downloads(user_id)
        remaining = max(0, verification.FREE_DOWNLOAD_LIMIT - downloads)
        
        await message.reply_text(
            f"📊 **Your Stats**\n\n"
            f"📥 **Downloads:** {downloads}\n"
            f"🎁 **Free remaining:** {remaining}\n"
            f"{'🔐 Verification required for next download' if remaining == 0 else '✅ Free downloads available'}"
        )

    # INTERCEPT LEECH COMMANDS
    original_leech = None

    async def enhanced_leech(client, message: Message):
        """Enhanced leech with verification"""
        from utils.verification import verification
        from utils.forwarder import forwarder
        
        user_id = message.from_user.id
        
        if len(message.command) < 2:
            await original_leech(client, message)
            return
        
        url = " ".join(message.command[1:])
        downloads = await verification.get_user_downloads(user_id)
        
        if verification.needs_verification(user_id, downloads):
            # Need verification
            token = await verification.create_token(user_id, url)
            shortlink = await verification.generate_shortlink(token)
            
            verify_text = f"""
🔐 **VERIFICATION REQUIRED**

You've used {verification.FREE_DOWNLOAD_LIMIT} free downloads!

**Steps:**
1. Click: {shortlink}
2. Complete shortlink
3. Use: `/verify {token}`

⏰ **Valid for:** {verification.format_time()}
🎯 **Token:** `{token}`
            """
            
            if verification.TUT_VID:
                verify_text += f"\n\n📺 **Tutorial:** {verification.TUT_VID}"
            
            await message.reply_text(verify_text)
            return
        
        # Track download
        await verification.increment_downloads(user_id)
        
        # Store info for forwarding
        message._forward_info = {"url": url, "user_id": user_id}
        
        # Call original leech
        await original_leech(client, message)

    # Hook into original leech command
    for handler in app.handlers:
        if hasattr(handler, 'callback') and handler.callback.__name__ == 'leech_command':
            original_leech = handler.callback
            handler.callback = enhanced_leech
            break

    # Hook into reply methods for forwarding
    original_reply_video = None
    original_reply_audio = None
    original_reply_document = None
    original_reply_photo = None

    async def forward_video(self, *args, **kwargs):
        sent = await original_reply_video(self, *args, **kwargs)
        if hasattr(self, '_forward_info'):
            from utils.forwarder import forwarder
            caption = kwargs.get('caption', '')
            filename = caption.split('**')[1] if '**' in caption else 'video'
            await forwarder.forward_file(app, sent, filename, self._forward_info['user_id'])
        return sent

    async def forward_audio(self, *args, **kwargs):
        sent = await original_reply_audio(self, *args, **kwargs)
        if hasattr(self, '_forward_info'):
            from utils.forwarder import forwarder
            caption = kwargs.get('caption', '')
            filename = caption.split('**')[1] if '**' in caption else 'audio'
            await forwarder.forward_file(app, sent, filename, self._forward_info['user_id'])
        return sent

    async def forward_document(self, *args, **kwargs):
        sent = await original_reply_document(self, *args, **kwargs)
        if hasattr(self, '_forward_info'):
            from utils.forwarder import forwarder
            caption = kwargs.get('caption', '')
            filename = caption.split('**')[1] if '**' in caption else 'document'
            await forwarder.forward_file(app, sent, filename, self._forward_info['user_id'])
        return sent

    async def forward_photo(self, *args, **kwargs):
        sent = await original_reply_photo(self, *args, **kwargs)
        if hasattr(self, '_forward_info'):
            from utils.forwarder import forwarder
            caption = kwargs.get('caption', '')
            filename = caption.split('**')[1] if '**' in caption else 'photo'
            await forwarder.forward_file(app, sent, filename, self._forward_info['user_id'])
        return sent

    # Store originals and replace
    from pyrogram.types import Message
    original_reply_video = Message.reply_video
    original_reply_audio = Message.reply_audio
    original_reply_document = Message.reply_document
    original_reply_photo = Message.reply_photo
    
    Message.reply_video = forward_video
    Message.reply_audio = forward_audio
    Message.reply_document = forward_document
    Message.reply_photo = forward_photo

    logger.info("✅ Verification handlers setup complete")
