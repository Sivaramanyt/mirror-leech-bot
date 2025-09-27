import logging
import os
from pyrogram import filters
from pyrogram.types import Message

logger = logging.getLogger(__name__)

def setup_verification_handlers(app):
    """Setup verification handlers (safe integration)"""
    
    # Import verification system
    try:
        from utils.verification import verification
    except ImportError:
        logger.warning("⚠️ Verification system not available")
        return
    
    @app.on_message(filters.command("verify") & filters.private)
    async def verify_command(client, message: Message):
        """Handle /verify token"""
        try:
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
                try:
                    from handlers.commands import leech_command
                    fake_message = message
                    fake_message.command = ["leech", result["url"]]
                    fake_message.text = f"/leech {result['url']}"
                    await leech_command(client, fake_message)
                except Exception as e:
                    logger.error(f"Leech after verification failed: {e}")
                    await message.reply_text("❌ **Download failed** - Please try again")
                
            else:
                await message.reply_text(f"❌ **Verification failed:** {result['error']}")
                
        except Exception as e:
            logger.error(f"Verify command error: {e}")
            await message.reply_text("❌ **Error occurred** - Please try again")

    @app.on_message(filters.command("mystats") & filters.private)
    async def stats_command(client, message: Message):
        """Show user stats"""
        try:
            user_id = message.from_user.id
            downloads = await verification.get_user_downloads(user_id)
            remaining = max(0, verification.FREE_DOWNLOAD_LIMIT - downloads)
            
            stats_text = f"""
📊 **YOUR STATISTICS**

👤 **User:** {message.from_user.first_name}
🆔 **ID:** `{user_id}`

📥 **Downloads:** {downloads} total
🎁 **Free Remaining:** {remaining} downloads
🔐 **Status:** {'Verification needed' if remaining == 0 else 'Free downloads available'}

⚙️ **Settings:**
• 🎁 Free Limit: {verification.FREE_DOWNLOAD_LIMIT} downloads  
• ⏰ Token Valid: {verification.format_time()}
• 🔐 Verification: {'ON' if verification.IS_VERIFY.lower() == 'true' else 'OFF'}

{'🎉 **Enjoy your free downloads!**' if remaining > 0 else '🔐 **Complete verification to continue**'}
            """
            
            await message.reply_text(stats_text)
            
        except Exception as e:
            logger.error(f"Stats command error: {e}")
            await message.reply_text("❌ **Error getting stats**")

    # ENHANCE EXISTING LEECH COMMAND
    def enhance_leech_command():
        """Enhance existing leech command with verification"""
        try:
            # Find existing leech handler
            original_leech = None
            for handler in app.handlers:
                if (hasattr(handler, 'callback') and 
                    hasattr(handler.callback, '__name__') and 
                    'leech' in handler.callback.__name__.lower()):
                    original_leech = handler.callback
                    break
            
            if not original_leech:
                logger.warning("⚠️ Original leech command not found")
                return
            
            async def enhanced_leech(client, message: Message):
                """Enhanced leech with verification check"""
                try:
                    user_id = message.from_user.id
                    
                    # Check if URL provided
                    if len(message.command) < 2:
                        await original_leech(client, message)
                        return
                    
                    url = " ".join(message.command[1:])
                    downloads = await verification.get_user_downloads(user_id)
                    
                    # Check if verification needed
                    if verification.needs_verification(downloads):
                        # Create verification token
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
                    message._verification_info = {
                        "url": url, 
                        "user_id": user_id,
                        "needs_forwarding": True
                    }
                    
                    # Call original leech
                    await original_leech(client, message)
                    
                except Exception as e:
                    logger.error(f"Enhanced leech error: {e}")
                    await original_leech(client, message)
            
            # Replace the handler
            for handler in app.handlers:
                if (hasattr(handler, 'callback') and 
                    hasattr(handler.callback, '__name__') and 
                    'leech' in handler.callback.__name__.lower()):
                    handler.callback = enhanced_leech
                    logger.info("✅ Leech command enhanced with verification")
                    break
                    
        except Exception as e:
            logger.error(f"Leech enhancement error: {e}")
    
    # Enhance existing leech command
    enhance_leech_command()
    
    # ADD FORWARDING TO REPLY METHODS
    def add_forwarding():
        """Add forwarding to reply methods"""
        try:
            from pyrogram.types import Message
            from utils.forwarder import forwarder
            
            # Store original methods
            original_reply_video = Message.reply_video
            original_reply_audio = Message.reply_audio
            original_reply_document = Message.reply_document
            original_reply_photo = Message.reply_photo
            
            async def reply_video_with_forward(self, *args, **kwargs):
                sent = await original_reply_video(self, *args, **kwargs)
                if hasattr(self, '_verification_info') and self._verification_info.get('needs_forwarding'):
                    caption = kwargs.get('caption', '')
                    filename = caption.split('**')[1] if '**' in caption else 'video'
                    await forwarder.forward_file(app, sent, filename, self._verification_info['user_id'])
                return sent
            
            async def reply_audio_with_forward(self, *args, **kwargs):
                sent = await original_reply_audio(self, *args, **kwargs)
                if hasattr(self, '_verification_info') and self._verification_info.get('needs_forwarding'):
                    caption = kwargs.get('caption', '')
                    filename = caption.split('**')[1] if '**' in caption else 'audio'
                    await forwarder.forward_file(app, sent, filename, self._verification_info['user_id'])
                return sent
            
            async def reply_document_with_forward(self, *args, **kwargs):
                sent = await original_reply_document(self, *args, **kwargs)
                if hasattr(self, '_verification_info') and self._verification_info.get('needs_forwarding'):
                    caption = kwargs.get('caption', '')
                    filename = caption.split('**')[1] if '**' in caption else 'document'
                    await forwarder.forward_file(app, sent, filename, self._verification_info['user_id'])
                return sent
            
            async def reply_photo_with_forward(self, *args, **kwargs):
                sent = await original_reply_photo(self, *args, **kwargs)
                if hasattr(self, '_verification_info') and self._verification_info.get('needs_forwarding'):
                    caption = kwargs.get('caption', '')
                    filename = caption.split('**')[1] if '**' in caption else 'photo'
                    await forwarder.forward_file(app, sent, filename, self._verification_info['user_id'])
                return sent
            
            # Replace methods
            Message.reply_video = reply_video_with_forward
            Message.reply_audio = reply_audio_with_forward
            Message.reply_document = reply_document_with_forward
            Message.reply_photo = reply_photo_with_forward
            
            logger.info("✅ Reply methods enhanced with forwarding")
            
        except Exception as e:
            logger.error(f"Forwarding enhancement error: {e}")
    
    # Add forwarding
    add_forwarding()
    
    logger.info("🎯 Verification handlers setup complete")
                    
