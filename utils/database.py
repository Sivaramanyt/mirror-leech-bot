import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.users = None
        self.tasks = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            database_url = os.environ.get("DATABASE_URL")
            database_name = os.environ.get("DATABASE_NAME", "terabox_bot")
            
            if database_url:
                self.client = AsyncIOMotorClient(database_url)
                self.db = self.client[database_name]
                self.users = self.db.users
                self.tasks = self.db.tasks
                logger.info("✅ Database connected successfully")
            else:
                logger.warning("⚠️ DATABASE_URL not provided, using in-memory storage")
                
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
    
    async def add_user(self, user_id, username=None):
        """Add user to database"""
        try:
            if self.users:
                user_data = {
                    "user_id": user_id,
                    "username": username,
                    "join_date": "2025-09-26"
                }
                await self.users.update_one(
                    {"user_id": user_id},
                    {"$set": user_data},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Error adding user: {e}")
    
    async def get_user(self, user_id):
        """Get user from database"""
        try:
            if self.users:
                return await self.users.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error getting user: {e}")
        return None

# Global database instance
db = Database()
            
