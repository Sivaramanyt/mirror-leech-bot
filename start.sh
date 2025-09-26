#!/bin/bash

# Mirror Leech Bot Startup Script
echo "🤖 Starting Mirror Leech Bot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Create necessary directories
mkdir -p downloads uploads logs

# Set permissions
chmod +x start.sh

# Check if required environment variables are set
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN is not set"
    exit 1
fi

if [ -z "$OWNER_ID" ]; then
    echo "❌ OWNER_ID is not set"  
    exit 1
fi

if [ -z "$TELEGRAM_API" ]; then
    echo "❌ TELEGRAM_API is not set"
    exit 1
fi

if [ -z "$TELEGRAM_HASH" ]; then
    echo "❌ TELEGRAM_HASH is not set"
    exit 1
fi

echo "✅ All required environment variables are set"

# Start the bot
echo "🚀 Starting bot..."
python3 bot.py
