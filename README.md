# 🤖 Mirror Leech Telegram Bot

A powerful but simplified Telegram bot for downloading and mirroring files from various sources, optimized for Koyeb free tier deployment with MongoDB integration.

## ✨ Features

### 📥 Supported Downloads
- **✅ Terabox** (videos/folders) - Working perfectly!
- **✅ YouTube** & 900+ sites via yt-dlp (Instagram, Twitter, TikTok, etc.)
- **✅ Direct HTTP/HTTPS** links
- **✅ Google Drive** links (public files/folders)
- **✅ Mega** links  
- **✅ MediaFire** links
- **✅ Torrent/Magnet** links
- **✅ Telegram** files

### 📤 Upload Destinations
- **Telegram** (with automatic file splitting)
- **Google Drive** (with service accounts support)

### ⚙️ Management Features
- Real-time progress tracking with live updates
- Queue system for multiple simultaneous downloads
- User authorization system (owner, sudo users, authorized chats)
- File size limits optimized for free tier (2GB)
- Cancel operations (individual or all)
- Status monitoring with system info
- Health check endpoint for Koyeb
- MongoDB integration for persistent storage

## 🚀 Quick Deployment on Koyeb

### Prerequisites
1. **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
2. **Telegram API ID & Hash** - Get from [my.telegram.org](https://my.telegram.org)
3. **MongoDB Atlas** (free) - Get from [mongodb.com](https://mongodb.com)
4. **GitHub Account** - For repository hosting

### Step 1: Setup Repository
1. **Fork this repository** or **create a new repository**
2. **Upload all bot files** to your repository
3. **Make repository public** (required for Koyeb free tier)

### Step 2: Setup MongoDB
1. Go to [MongoDB Atlas](https://mongodb.com) and create free account
2. Create a **free cluster** (M0 Sandbox)
3. Create a **database user** with read/write permissions
4. Get the **connection string** (looks like: `mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/`)
5. **Whitelist all IPs** (0.0.0.0/0) in Network Access

### Step 3: Deploy on Koyeb
1. Go to [Koyeb](https://koyeb.com) and create free account
2. Click **"Create App"** → **"Deploy from GitHub"**
3. Connect your GitHub account and select your repository
4. Configure the deployment:
   - **Service type**: Web Service
   - **Instance type**: Nano (Free tier)
   - **Port**: 8000
   - **Health check**: `/health`

### Step 4: Environment Variables
Set these **required** environment variables in Koyeb:

```bash
# Required Variables
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
OWNER_ID=123456789
TELEGRAM_API=1234567
TELEGRAM_HASH=abcdef1234567890abcdef1234567890
DATABASE_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
PORT=8000
```

### Step 5: Optional Variables
```bash
# Google Drive (Optional)
GDRIVE_ID=your_google_drive_folder_id
IS_TEAM_DRIVE=False
USE_SERVICE_ACCOUNTS=False

# Authorization (Optional)
AUTHORIZED_CHATS=chat_id1 chat_id2
SUDO_USERS=user_id1 user_id2

# Upload Settings (Optional)
DEFAULT_UPLOAD=tg
LEECH_DUMP_CHAT=@your_channel
LEECH_SPLIT_SIZE=2147483648
AS_DOCUMENT=False

# Limits (Optional)
MAX_FILE_SIZE=2147483648
QUEUE_ALL=8
QUEUE_DOWNLOAD=4
QUEUE_UPLOAD=4

# Other (Optional)
CMD_SUFFIX=
EXCLUDED_EXTENSIONS=.zip .rar
STATUS_UPDATE_INTERVAL=10
```

## 📋 Bot Commands

### 📥 Download Commands
- `/mirror [link]` - Mirror files to Google Drive
- `/leech [link]` - Upload files to Telegram
- `/ytdl [link]` - Download from YouTube and 900+ sites

### 📊 Management Commands  
- `/status` - Show active downloads with progress
- `/cancel [task_id]` - Cancel a specific download
- `/cancelall` - Cancel all active downloads
- `/ping` - Check bot response time and status

### 🔧 Admin Commands (Owner/Sudo only)
- `/auth [user_id]` - Authorize a user to use the bot
- `/unauth [user_id]` - Remove user authorization  
- `/users` - List all authorized users
- `/log` - Get bot log file
- `/restart` - Restart the bot (owner only)

### 📚 Help Commands
- `/start` - Welcome message with basic info
- `/help` - Detailed help with examples

## 💡 Usage Examples

```bash
# Mirror a Terabox video to Google Drive
/mirror https://terabox.com/s/1ABCDefGhIjKlMnOpQrStUvWxYz

# Leech a direct file to Telegram
/leech https://example.com/file.zip

# Download YouTube video
/ytdl https://youtube.com/watch?v=dQw4w9WgXcQ

# Check download status
/status

# Cancel a specific download
/cancel task_1

# Authorize a user (owner only)
/auth 123456789
```

## 🔧 Advanced Configuration

### Google Drive Setup (Optional)
1. **Create Google Drive credentials** following [this guide](https://developers.google.com/drive/api/v3/quickstart/python)
2. **Place `credentials.json`** in repository root
3. **Run `python generate_drive_token.py`** locally to generate `token.pickle`  
4. **Upload `token.pickle`** to repository
5. **Set environment variables**:
   ```bash
   GDRIVE_ID=your_folder_id
   IS_TEAM_DRIVE=False
   ```

### Service Accounts (For Heavy Usage)
1. **Create service accounts** following Google's documentation
2. **Place JSON files** in `accounts/` folder
3. **Set environment variable**: `USE_SERVICE_ACCOUNTS=True`

### Custom Upload Chat
Set files to be uploaded to a specific chat/channel:
```bash
LEECH_DUMP_CHAT=-100123456789  # Channel ID
# or
LEECH_DUMP_CHAT=@your_channel  # Channel username
```

## 🐳 Local Development with Docker

### Using Docker Compose
```bash
# Clone repository
git clone <your-repo-url>
cd mirror-leech-bot

# Copy environment file
cp .env.example .env
# Edit .env with your values

# Build and run
docker-compose up --build
```

### Using Docker directly
```bash
# Build image
docker build -t mirror-leech-bot .

# Run container
docker run --env-file .env -p 8000:8000 mirror-leech-bot
```

## 📱 Mobile-Friendly Development

This bot is specifically designed for **mobile-only development**:
- All configurations via environment variables
- No complex local setup required
- Optimized for free tier deployments
- Health check endpoint for monitoring
- Minimal resource usage

## ⚠️ Important Notes

### Free Tier Limitations
- **File size limit**: 2GB per file
- **Concurrent downloads**: Limited by free tier resources
- **Storage**: Temporary (files auto-deleted after upload)
- **Bandwidth**: Limited by Koyeb/MongoDB free tiers

### Supported File Types
- **Videos**: MP4, MKV, AVI, MOV, etc.
- **Documents**: PDF, DOC, ZIP, RAR, etc.
- **Images**: JPG, PNG, GIF, etc.
- **Audio**: MP3, FLAC, M4A, etc.
- **Archives**: ZIP, RAR, 7Z, TAR, etc.

### Security Features  
- **User authorization** system
- **Owner-only** commands for sensitive operations
- **Chat restrictions** for private usage
- **Input validation** and sanitization
- **Rate limiting** via queue system

## 🐛 Troubleshooting

### Common Issues

**1. "Failed to get file info from any endpoint"**
- Check if Terabox link is valid and accessible
- Try using a different Terabox link
- Terabox might be blocking requests (temporary issue)

**2. "Database connection failed"**
- Verify MongoDB connection string is correct
- Check if database user has proper permissions
- Ensure IP whitelist includes 0.0.0.0/0

**3. "Google Drive upload failed"**
- Verify `GDRIVE_ID` is correct
- Check if `token.pickle` or service accounts are properly set up
- Ensure Drive folder has proper permissions

**4. "Bot not responding"**
- Check if bot is authorized in the chat
- Verify environment variables are set correctly
- Check Koyeb logs for errors

**5. "Health check failing"**
- Ensure `PORT` environment variable matches Koyeb service port (8000)
- Check if health check endpoint is accessible

### Getting Logs
```bash
# From bot (if running)
/log

# From Koyeb dashboard
Go to your app → Logs tab

# From Docker
docker logs <container_id>
```

## 🔄 Updates and Maintenance

### Updating the Bot
1. **Pull latest changes** from repository
2. **Redeploy on Koyeb** (automatic if connected to GitHub)
3. **Check for new environment variables** in README

### Database Maintenance
- **MongoDB Atlas** free tier auto-manages backups
- **Clean old tasks** periodically (handled automatically)
- **Monitor usage** via MongoDB Atlas dashboard

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original repository**: [anasty17/mirror-leech-telegram-bot](https://github.com/anasty17/mirror-leech-telegram-bot)
- **Pyrogram**: Telegram bot framework
- **yt-dlp**: YouTube and media downloading
- **MongoDB**: Database for persistent storage
- **Koyeb**: Free tier hosting platform

## 🆘 Support

For issues, questions, or feature requests:
1. **Check existing issues** in the repository
2. **Create a new issue** with detailed description
3. **Provide logs** and environment details
4. **Be patient** - this is a community project

---

**⭐ Star this repository if you find it helpful!**

**🔄 Share with others who might benefit from this bot!**
