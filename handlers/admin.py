import logging
from datetime import datetime
from pyrogram import filters, Client
from pyrogram.types import Message
from utils.database import db
from utils.verification import verification_manager
from config import OWNER_ID

logger = logging.getLogger(__name__)

# Admin command handlers
@Client.on_message(filters.command("setshortlink") & filters.user(OWNER_ID))
async def set_shortlink_command(client: Client, message: Message):
    """Set shortlink URL with API key"""
    try:
        if len(message.text.split()) < 2:
            await message.reply_text(
                "❌ **Usage:** `/setshortlink [full_url_with_api]`\n\n"
                "**Example:** `/setshortlink https://gplinks.co/st?api=YOUR_API_KEY&url=`"
            )
            return
        
        shortlink_url = message.text.split(maxsplit=1)[1]
        
        # Validate URL format
        if not shortlink_url.startswith("http"):
            await message.reply_text("❌ Invalid URL format. Must start with http:// or https://")
            return
        
        # Update or insert setting
        await db.bot_settings_new.update_one(
            {"setting_name": "shortlink_url"},
            {
                "$set": {
                    "setting_name": "shortlink_url",
                    "value": shortlink_url,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        await message.reply_text(f"✅ **Shortlink URL updated successfully!**\n\n📎 **URL:** `{shortlink_url}`")
        logger.info(f"🔗 Shortlink URL updated by admin: {shortlink_url}")
        
    except Exception as e:
        await message.reply_text(f"❌ **Error updating shortlink:** {e}")
        logger.error(f"❌ Error in setshortlink command: {e}")

@Client.on_message(filters.command("setvalidity") & filters.user(OWNER_ID))
async def set_validity_command(client: Client, message: Message):
    """Set verification validity hours"""
    try:
        if len(message.text.split()) < 2:
            await message.reply_text(
                "❌ **Usage:** `/setvalidity [hours]`\n\n"
                "**Examples:**\n"
                "• `/setvalidity 2` - 2 hours\n"
                "• `/setvalidity 12` - 12 hours\n"
                "• `/setvalidity 24` - 24 hours"
            )
            return
        
        hours_str = message.text.split()[1].rstrip('h')
        hours = int(hours_str)
        
        if hours < 1 or hours > 168:  # 1 hour to 7 days
            await message.reply_text("❌ **Validity must be between 1 hour and 168 hours (7 days)**")
            return
        
        # Update or insert setting
        await db.bot_settings_new.update_one(
            {"setting_name": "verification_validity"},
            {
                "$set": {
                    "setting_name": "verification_validity",
                    "value": hours,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        await message.reply_text(f"✅ **Verification validity updated!**\n\n⏰ **Duration:** {hours} hours")
        logger.info(f"⏰ Verification validity updated to {hours} hours")
        
    except ValueError:
        await message.reply_text("❌ **Invalid number format. Please enter a valid number.**")
    except Exception as e:
        await message.reply_text(f"❌ **Error updating validity:** {e}")
        logger.error(f"❌ Error in setvalidity command: {e}")

@Client.on_message(filters.command("adminstatus") & filters.user(OWNER_ID))
async def admin_status_command(client: Client, message: Message):
    """Show current bot settings"""
    try:
        settings = await db.bot_settings_new.find().to_list(None)
        
        # Get statistics
        total_users = await db.users_verification.count_documents({})
        verified_users = await db.users_verification.count_documents({"verification_status": True})
        total_files = await db.forwarded_files.count_documents({})
        
        status_text = "📊 **ADMIN DASHBOARD**\n\n"
        status_text += "⚙️ **Current Settings:**\n"
        
        for setting in settings:
            setting_name = setting["setting_name"].replace("_", " ").title()
            if setting["setting_name"] == "shortlink_url":
                # Mask API key for security
                value = setting["value"]
                if "api=" in value and "&" in value:
                    masked_value = value.split("api=")[0] + "api=***HIDDEN***" + value.split("&url=")[1] if "&url=" in value else value
                else:
                    masked_value = value
                status_text += f"• **{setting_name}:** `{masked_value}`\n"
            else:
                status_text += f"• **{setting_name}:** `{setting['value']}`\n"
        
        status_text += f"\n📈 **Statistics:**\n"
        status_text += f"• **Total Users:** {total_users}\n"
        status_text += f"• **Verified Users:** {verified_users}\n"
        status_text += f"• **Files in Channel:** {total_files}\n"
        
        await message.reply_text(status_text)
        
    except Exception as e:
        await message.reply_text(f"❌ **Error getting status:** {e}")
        logger.error(f"❌ Error in adminstatus command: {e}")

@Client.on_message(filters.command("resetuser") & filters.user(OWNER_ID))
async def reset_user_command(client: Client, message: Message):
    """Reset user verification status"""
    try:
        if len(message.text.split()) < 2:
            await message.reply_text(
                "❌ **Usage:** `/resetuser [user_id]`\n\n"
                "**Example:** `/resetuser 123456789`"
            )
            return
        
        user_id = int(message.text.split()[1])
        success = await verification_manager.reset_user_verification(user_id)
        
        if success:
            await message.reply_text(f"✅ **User verification reset successfully!**\n\n👤 **User ID:** `{user_id}`")
        else:
            await message.reply_text(f"❌ **Failed to reset user verification**")
        
    except ValueError:
        await message.reply_text("❌ **Invalid user ID format. Please enter a valid number.**")
    except Exception as e:
        await message.reply_text(f"❌ **Error resetting user:** {e}")
        logger.error(f"❌ Error in resetuser command: {e}")

@Client.on_message(filters.command("setchannel") & filters.user(OWNER_ID))
async def set_channel_command(client: Client, message: Message):
    """Set private channel ID"""
    try:
        if len(message.text.split()) < 2:
            await message.reply_text(
                "❌ **Usage:** `/setchannel [channel_id]`\n\n"
                "**Example:** `/setchannel -1001234567890`"
            )
            return
        
        channel_id = message.text.split()[1]
        
        # Validate channel ID format
        if not (channel_id.startswith("-100") or channel_id.startswith("@")):
            await message.reply_text("❌ **Invalid channel ID format. Should start with -100 or @**")
            return
        
        # Update or insert setting
        await db.bot_settings_new.update_one(
            {"setting_name": "private_channel_id"},
            {
                "$set": {
                    "setting_name": "private_channel_id", 
                    "value": channel_id,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        await message.reply_text(f"✅ **Private channel ID updated!**\n\n📁 **Channel:** `{channel_id}`")
        logger.info(f"📁 Private channel updated: {channel_id}")
        
    except Exception as e:
        await message.reply_text(f"❌ **Error updating channel:** {e}")
        logger.error(f"❌ Error in setchannel command: {e}")

@Client.on_message(filters.command("cleanup") & filters.user(OWNER_ID))
async def cleanup_command(client: Client, message: Message):
    """Manually trigger file cleanup"""
    try:
        from utils.file_manager import file_manager
        
        await message.reply_text("🧹 **Starting cleanup process...**")
        await file_manager.cleanup_expired_files(client)
        await message.reply_text("✅ **Cleanup completed!**")
        
    except Exception as e:
        await message.reply_text(f"❌ **Cleanup error:** {e}")
        logger.error(f"❌ Error in cleanup command: {e}")
