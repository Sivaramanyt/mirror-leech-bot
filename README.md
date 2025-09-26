# 🤖 Mirror Leech Telegram Bot

A simplified but powerful Telegram bot for downloading and mirroring files from various sources.

## ✨ Features

### 📥 Supported Downloads
- **Terabox** (videos/folders) ✅
- **YouTube** & 900+ sites via yt-dlp
- **Direct HTTP/HTTPS** links
- **Google Drive** links
- **Mega** links  
- **MediaFire** links
- **Torrent/Magnet** links
- **Telegram** files

### 📤 Upload Destinations
- **Telegram** (with auto-splitting)
- **Google Drive** (with service accounts)

### ⚙️ Management
- Progress tracking with live updates
- Queue system for multiple downloads
- User authorization system
- File size limits for free tier
- Cancel operations
- Status monitoring

## 🚀 Deployment on Koyeb

1. **Fork this repository**
2. **Connect to Koyeb:**
   - Go to [Koyeb](https://koyeb.com)
   - Create new app from GitHub
   - Select your forked repository

3. **Set Environment Variables:**

BOT_TOKEN=your_bot_token
OWNER_ID=your_telegram_user_id
TELEGRAM_API=your_api_id
TELEGRAM_HASH=your_api_hash
DATABASE_URL=your_mongodb_connection_string
PORT=8000

4. **Optional Variables:**

GDRIVE_ID=your_google_drive_folder_id
AUTHORIZED_CHATS=chat_id1 chat_id2
LEECH_DUMP_CHAT=channel_or_chat_id
MAX_FILE_SIZE=2147483648

## 📋 Commands

- `/mirror [link]` - Mirror to Google Drive
- `/leech [link]` - Upload to Telegram  
- `/ytdl [link]` - Download from YouTube/social media
- `/status` - Check active downloads
- `/cancel [gid]` - Cancel download
- `/auth [user_id]` - Authorize user (owner only)
- `/ping` - Check bot status

## 🔧 Setup MongoDB

1. Go to [MongoDB Atlas](https://mongodb.com)
2. Create free cluster
3. Get connection string
4. Add to `DATABASE_URL` environment variable

## 📱 Mobile-Friendly

This bot is optimized for:
- Koyeb free tier deployment
- Mobile-only development
- MongoDB Atlas free tier
- Automatic health checks

## ⚠️ Limitations

- 2GB file size limit (free tier)
- No QBittorrent web interface
- Basic torrent support only
- No RSS monitoring

## 🆘 Support

For issues and updates, check the GitHub repository.
