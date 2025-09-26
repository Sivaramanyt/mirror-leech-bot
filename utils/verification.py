import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from utils.database import db

logger = logging.getLogger(__name__)

class VerificationManager:
    def __init__(self):
        self.free_uses_limit = 3
    
    async def check_user_verification(self, user_id: int) -> bool:
        """Check if user needs verification (File Store Bot method)"""
        try:
            # Get user verification data
            user_data = await db.users_verification.find_one({"user_id": user_id})
            
            if not user_data:
                # New user - create record with 0 usage
                await db.users_verification.insert_one({
                    "user_id": user_id,
                    "usage_count": 0,
                    "verification_status": False,
                    "verified_at": None,
                    "verification_expires": None,
                    "last_used": datetime.utcnow()
                })
                return False  # First use is free
            
            # Check if user has free uses remaining
            if user_data["usage_count"] < self.free_uses_limit:
                # Increment usage count
                await db.users_verification.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {"usage_count": 1},
                        "$set": {"last_used": datetime.utcnow()}
                    }
                )
                logger.info(f"✅ Free use {user_data['usage_count'] + 1}/3 for user {user_id}")
                return False  # Still free
            
            # User needs verification - check if already verified and not expired
            if user_data.get("verification_status") and user_data.get("verification_expires"):
                if datetime.utcnow() < user_data["verification_expires"]:
                    logger.info(f"✅ User {user_id} already verified, access granted")
                    return False  # Verification still valid
                else:
                    # Verification expired
                    await db.users_verification.update_one(
                        {"user_id": user_id},
                        {"$set": {"verification_status": False, "verification_expires": None}}
                    )
                    logger.info(f"⏰ Verification expired for user {user_id}")
            
            logger.info(f"🔗 Verification required for user {user_id}")
            return True  # Needs verification
            
        except Exception as e:
            logger.error(f"❌ Error checking verification for user {user_id}: {e}")
            return False  # Default to allow on error
    
    async def generate_verification_link(self, user_id: int) -> str:
        """Generate verification shortlink (File Store Bot method)"""
        try:
            # Create unique verification token
            verification_token = f"verify_{user_id}_{int(time.time())}"
            
            # Store verification token in database
            await db.verification_tokens.insert_one({
                "token": verification_token,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "is_verified": False,
                "verified_at": None
            })
            
            # Get shortlink settings from database
            shortlink_setting = await db.bot_settings_new.find_one({"setting_name": "shortlink_url"})
            
            if not shortlink_setting:
                # Default shortlink - admin needs to set this
                await db.bot_settings_new.insert_one({
                    "setting_name": "shortlink_url",
                    "value": "https://example.com/shortlink?url=",  # Admin will update
                    "updated_at": datetime.utcnow()
                })
                shortlink_url = "https://example.com/shortlink?url="
            else:
                shortlink_url = shortlink_setting["value"]
            
            # Create callback URL (back to your bot)
            from config import BOT_USERNAME
            callback_url = f"https://t.me/{BOT_USERNAME}?start={verification_token}"
            
            # Generate shortlink using admin's manual setting
            verification_link = f"{shortlink_url}{callback_url}"
            
            logger.info(f"🔗 Generated verification link for user {user_id}")
            return verification_link
            
        except Exception as e:
            logger.error(f"❌ Error generating verification link for user {user_id}: {e}")
            return "Error generating verification link. Contact admin."
    
    async def handle_verification_callback(self, verification_token: str, user_id: int):
        """Handle user returning after verification (File Store Bot method)"""
        try:
            # Find and verify the token
            token_data = await db.verification_tokens.find_one({
                "token": verification_token,
                "user_id": user_id,
                "is_verified": False
            })
            
            if not token_data:
                logger.warning(f"⚠️ Invalid or already used token: {verification_token}")
                return False
            
            # Mark token as verified
            await db.verification_tokens.update_one(
                {"token": verification_token},
                {
                    "$set": {
                        "is_verified": True,
                        "verified_at": datetime.utcnow()
                    }
                }
            )
            
            # Get verification validity hours from settings
            validity_setting = await db.bot_settings_new.find_one({"setting_name": "verification_validity"})
            validity_hours = validity_setting["value"] if validity_setting else 12  # Default 12 hours
            
            # Update user verification status
            expires_at = datetime.utcnow() + timedelta(hours=validity_hours)
            await db.users_verification.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "verification_status": True,
                        "verified_at": datetime.utcnow(),
                        "verification_expires": expires_at
                    }
                }
            )
            
            logger.info(f"✅ User {user_id} verification completed, valid until {expires_at}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling verification callback: {e}")
            return False
    
    async def reset_user_verification(self, user_id: int):
        """Reset user verification status (admin command)"""
        try:
            await db.users_verification.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "usage_count": 0,
                        "verification_status": False,
                        "verified_at": None,
                        "verification_expires": None,
                        "last_used": datetime.utcnow()
                    }
                }
            )
            logger.info(f"🔄 Reset verification for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Error resetting user {user_id}: {e}")
            return False

# Initialize verification manager
verification_manager = VerificationManager()
