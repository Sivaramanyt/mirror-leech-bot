import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        # Existing collections (your current ones - untouched)
        self.users = None
        
        # NEW collections for premium features (added, not modified)
        self.users_verification = None
        self.verification_tokens = None
        self.bot_settings_new = None
        self.forwarded_files = None
        
    async def connect(self):
        """Connect to MongoDB database"""
        try:
            # Get database connection details from environment
            database_url = os.environ.get("DATABASE_URL")
            database_name = os.environ.get("DATABASE_NAME", "terabox_bot")
            
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            # Connect to MongoDB
            self.client = AsyncIOMotorClient(database_url)
            self.db = self.client[database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("✅ Database connected successfully")
            
            # Initialize collections
            await self._initialize_collections()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def _initialize_collections(self):
        """Initialize all database collections"""
        try:
            # Existing collections (your current ones - preserved)
            if hasattr(self.db, 'users'):
                self.users = self.db.users
                logger.info("✅ Existing users collection initialized")
            
            # NEW collections for premium features
            self.users_verification = self.db.users_verification
            self.verification_tokens = self.db.verification_tokens
            self.bot_settings_new = self.db.bot_settings_new
            self.forwarded_files = self.db.forwarded_files
            
            # Create indexes for better performance
            await self._create_indexes()
            
            # Initialize default settings
            await self._initialize_default_settings()
            
            logger.info("✅ All database collections initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing collections: {e}")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Index for users_verification collection
            await self.users_verification.create_index("user_id", unique=True)
            await self.users_verification.create_index("verification_expires")
            
            # Index for verification_tokens collection
            await self.verification_tokens.create_index("token", unique=True)
            await self.verification_tokens.create_index("user_id")
            await self.verification_tokens.create_index("created_at")
            
            # Index for bot_settings_new collection
            await self.bot_settings_new.create_index("setting_name", unique=True)
            
            # Index for forwarded_files collection
            await self.forwarded_files.create_index("channel_msg_id", unique=True)
            await self.forwarded_files.create_index("auto_delete_at")
            await self.forwarded_files.create_index("created_at")
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
    
    async def _initialize_default_settings(self):
        """Initialize default bot settings"""
        try:
            default_settings = [
                {
                    "setting_name": "shortlink_url",
                    "value": "https://example.com/shortlink?url=",  # Admin will update this
                    "updated_at": datetime.utcnow(),
                    "description": "Shortlink service URL with API key"
                },
                {
                    "setting_name": "verification_validity",
                    "value": 12,  # 12 hours default
                    "updated_at": datetime.utcnow(),
                    "description": "Verification validity in hours"
                },
                {
                    "setting_name": "private_channel_id", 
                    "value": "-1003068078005",  # Your channel ID
                    "updated_at": datetime.utcnow(),
                    "description": "Private channel for anonymous file forwarding"
                },
                {
                    "setting_name": "auto_delete_hours",
                    "value": 24,  # 24 hours default
                    "updated_at": datetime.utcnow(),
                    "description": "Auto-delete files after X hours"
                },
                {
                    "setting_name": "free_uses_limit",
                    "value": 3,  # 3 free uses
                    "updated_at": datetime.utcnow(),
                    "description": "Number of free uses before verification"
                }
            ]
            
            for setting in default_settings:
                existing = await self.bot_settings_new.find_one({"setting_name": setting["setting_name"]})
                if not existing:
                    await self.bot_settings_new.insert_one(setting)
                    logger.info(f"✅ Default setting initialized: {setting['setting_name']}")
            
            logger.info("✅ Default settings initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing default settings: {e}")
    
    async def get_setting(self, setting_name: str, default_value=None):
        """Get a bot setting value"""
        try:
            setting = await self.bot_settings_new.find_one({"setting_name": setting_name})
            return setting["value"] if setting else default_value
        except Exception as e:
            logger.error(f"❌ Error getting setting {setting_name}: {e}")
            return default_value
    
    async def update_setting(self, setting_name: str, value, description: str = None):
        """Update a bot setting"""
        try:
            update_data = {
                "setting_name": setting_name,
                "value": value,
                "updated_at": datetime.utcnow()
            }
            
            if description:
                update_data["description"] = description
            
            result = await self.bot_settings_new.update_one(
                {"setting_name": setting_name},
                {"$set": update_data},
                upsert=True
            )
            
            logger.info(f"✅ Setting updated: {setting_name} = {value}")
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"❌ Error updating setting {setting_name}: {e}")
            return False
    
    async def get_user_verification(self, user_id: int):
        """Get user verification data"""
        try:
            return await self.users_verification.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"❌ Error getting user verification {user_id}: {e}")
            return None
    
    async def update_user_verification(self, user_id: int, update_data: dict):
        """Update user verification data"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.users_verification.update_one(
                {"user_id": user_id},
                {"$set": update_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"❌ Error updating user verification {user_id}: {e}")
            return False
    
    async def cleanup_expired_tokens(self):
        """Clean up expired verification tokens (older than 24 hours)"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            result = await self.verification_tokens.delete_many({
                "created_at": {"$lt": cutoff_time},
                "is_verified": False
            })
            
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned up {result.deleted_count} expired tokens")
            
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired tokens: {e}")
            return 0
    
    async def get_statistics(self):
        """Get bot statistics"""
        try:
            stats = {}
            
            # User statistics
            stats["total_users"] = await self.users_verification.count_documents({})
            stats["verified_users"] = await self.users_verification.count_documents({"verification_status": True})
            stats["active_verifications"] = await self.users_verification.count_documents({
                "verification_status": True,
                "verification_expires": {"$gt": datetime.utcnow()}
            })
            
            # File statistics
            stats["total_files"] = await self.forwarded_files.count_documents({})
            stats["files_today"] = await self.forwarded_files.count_documents({
                "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            # Token statistics
            stats["active_tokens"] = await self.verification_tokens.count_documents({"is_verified": False})
            stats["verified_tokens"] = await self.verification_tokens.count_documents({"is_verified": True})
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}
    
    async def close(self):
        """Close database connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("✅ Database connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing database: {e}")

# Initialize database instance
database = Database()
db = database  # For backward compatibility

# Expose collections for direct access (backward compatibility)
async def get_db():
    """Get database instance"""
    if not database.db:
        await database.connect()
    return database

# Initialize database connection
async def init_database():
    """Initialize database connection"""
    success = await database.connect()
    if not success:
        raise Exception("Failed to connect to database")
    return database

# Cleanup function for scheduled tasks
async def cleanup_database():
    """Run periodic cleanup tasks"""
    try:
        # Clean up expired tokens
        await database.cleanup_expired_tokens()
        
        # Clean up expired verification status
        current_time = datetime.utcnow()
        expired_users = await database.users_verification.update_many(
            {
                "verification_status": True,
                "verification_expires": {"$lt": current_time}
            },
            {
                "$set": {
                    "verification_status": False,
                    "verification_expires": None
                }
            }
        )
        
        if expired_users.modified_count > 0:
            logger.info(f"🧹 Expired {expired_users.modified_count} user verifications")
        
        logger.info("✅ Database cleanup completed")
        
    except Exception as e:
        logger.error(f"❌ Database cleanup error: {e}")
