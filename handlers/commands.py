@app.on_message(filters.command("leech"))
async def leech_command(client, message: Message):
    """Real Terabox leech command"""
    try:
        from utils.terabox import terabox_downloader
        
        user_id = message.from_user.id
        
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **Please provide a Terabox URL**\n\n"
                "**Usage:** `/leech [URL]`\n"
                "**Example:** `/leech https://terabox.com/s/abc123`"
            )
            return
        
        url = " ".join(message.command[1:])
        
        if not validators.url(url):
            await message.reply_text("❌ Invalid URL format")
            return
        
        if not terabox_downloader.is_supported_domain(url):
            await message.reply_text("❌ Only Terabox URLs are supported")
            return
        
        # Start process
        status_msg = await message.reply_text("🔍 **Getting file info...**")
        
        # Get file info
        file_info = await terabox_downloader.extract_file_info(url)
        
        if not file_info.get("success"):
            await status_msg.edit_text(f"❌ **Error:** {file_info.get('error')}")
            return
        
        await status_msg.edit_text(
            f"✅ **File Found!**\n\n"
            f"📁 **Name:** {file_info['filename']}\n"
            f"🔗 **Source:** Terabox\n\n"
            f"📥 **Starting download...**"
        )
        
        # Progress callback
        async def progress_callback(downloaded, total):
            try:
                progress = (downloaded / total) * 100
                await status_msg.edit_text(
                    f"📥 **Downloading...**\n\n"
                    f"📁 **File:** {file_info['filename'][:30]}...\n"
                    f"📊 **Progress:** {progress:.1f}%\n"
                    f"⬇️ **Downloaded:** {terabox_downloader.get_readable_file_size(downloaded)}"
                )
            except:
                pass
        
        # Download file
        download_path = await terabox_downloader.download_file(url, progress_callback)
        
        if download_path and os.path.exists(download_path):
            file_size = os.path.getsize(download_path)
            await status_msg.edit_text(
                f"✅ **Download Complete!**\n\n"
                f"📁 **File:** {file_info['filename']}\n"
                f"📊 **Size:** {terabox_downloader.get_readable_file_size(file_size)}\n"
                f"💾 **Saved to:** Server\n\n"
                f"🚀 **Ready for upload to Telegram!**"
            )
        else:
            await status_msg.edit_text("❌ Download failed")
            
        logger.info(f"📥 Leech completed for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Leech error: {e}")
        await message.reply_text("❌ An error occurred during download")
            
