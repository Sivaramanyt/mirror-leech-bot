@app.on_message(filters.command("leech"))
async def leech_command(client, message: Message):
    """Real leech command with Terabox API"""
    try:
        from utils.terabox import terabox  # Import here to avoid circular imports
        
        user_id = message.from_user.id
        
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **Please provide a URL to download**\n\n"
                "**Usage:** `/leech [URL]`\n"
                "**Example:** `/leech https://terabox.com/s/abc123`\n\n"
                "💡 **Tip:** Send Terabox URLs directly!"
            )
            return
        
        url = " ".join(message.command[1:])
        
        if not validators.url(url):
            await message.reply_text("❌ Invalid URL format")
            return
        
        # Processing message
        status_msg = await message.reply_text("🔍 **Analyzing Terabox URL...**")
        
        # Get file info from Terabox
        file_info = await terabox.get_file_info(url)
        
        if not file_info["success"]:
            await status_msg.edit_text(
                f"❌ **Error:** {file_info['error']}\n\n"
                "**Possible causes:**\n"
                "• Private or restricted file\n"
                "• Invalid/expired URL\n"
                "• File not found\n\n"
                "Try with a different URL."
            )
            return
        
        # Success - show file info
        await status_msg.edit_text(
            f"✅ **File Found!**\n\n"
            f"📁 **Name:** {file_info['filename']}\n"
            f"📊 **Size:** {terabox.format_size(file_info['size'])}\n"
            f"🔗 **Type:** {file_info['file_type']}\n\n"
            f"🚀 **Status:** Ready for download!\n"
            f"📥 **URL:** Valid Terabox link detected\n\n"
            f"🔧 **Next:** File upload to Telegram will be implemented next.\n"
            f"**This confirms the Terabox API is working!** ✅"
        )
        
        logger.info(f"📥 Real leech processed for user {user_id}: {file_info['filename']}")
        
    except Exception as e:
        logger.error(f"❌ Leech error: {e}")
        await message.reply_text(
            "❌ **Error occurred**\n\n"
            "Please try again or contact support."
        )
        
