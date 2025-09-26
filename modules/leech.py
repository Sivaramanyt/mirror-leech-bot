async def upload_to_telegram(self, file_path: str, message: Message, task_id: str):
    """Upload file to Telegram with proper video/document detection"""
    try:
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Get file extension
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Define file type categories
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Check file size limit
        if file_size > config.MAX_FILE_SIZE:
            await message.reply_text(f"❌ File too large: {get_readable_file_size(file_size)}")
            return
        
        # Upload based on file type
        if file_ext in video_extensions:
            # Send as VIDEO with streaming support
            logger.info(f"📹 Uploading as video: {filename}")
            await message.reply_video(
                video=file_path,
                caption=f"🎥 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                parse_mode=ParseMode.HTML,
                supports_streaming=True,  # Enable streaming
                duration=0,  # Telegram will detect automatically
                width=0,     # Telegram will detect automatically  
                height=0     # Telegram will detect automatically
            )
            
        elif file_ext in audio_extensions:
            # Send as AUDIO
            await message.reply_audio(
                audio=file_path,
                caption=f"🎵 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                parse_mode=ParseMode.HTML
            )
            
        elif file_ext in image_extensions:
            # Send as PHOTO
            await message.reply_photo(
                photo=file_path,
                caption=f"🖼️ <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                parse_mode=ParseMode.HTML
            )
        else:
            # Send as DOCUMENT
            await message.reply_document(
                document=file_path,
                caption=f"📄 <b>{filename}</b>\n📦 <b>Size:</b> {get_readable_file_size(file_size)}",
                parse_mode=ParseMode.HTML
            )
        
        # Success message
        await message.reply_text("✅ **Leech completed successfully!**", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await message.reply_text(f"❌ Upload failed: {str(e)}")
    
