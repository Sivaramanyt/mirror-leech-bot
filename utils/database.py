import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, Dict, Any
from .config import DATABASE_URL, DATABASE_NAME, FEATURES

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.users = None
        self.downloads = None
        self.stats = None
        self.enabled = FEATURES.get("database_enabled", False)
        
    async def connect(self):
        """Connect to MongoDB"""
        if not self.enabled or not DATABASE_URL:
            logger.warning("⚠️ Database not configured - running without database")
            return False
            
        try:
            self.client = AsyncIOMotorClient(DATABASE_URL)
            self.db = self.client[DATABASE_NAME]
            
            # Initialize collections
            self.users = self.db.users
            self.downloads = self.db.downloads
            self.stats = self.db.stats
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("✅ Database connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.enabled = False
            return False
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("🔒 Database connection closed")
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user in database"""
        if not self.enabled:
            return
            
        try:
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "join_date": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "total_downloads": 0
            }
            
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": user_data, "$setOnInsert": {"join_date": datetime.utcnow()}},
                upsert=True
            )
            logger.info(f"👤 User {user_id} added/updated in database")
            
        except Exception as e:
            logger.error(f"❌ Error adding user to database: {e}")
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user from database"""
        if not self.enabled:
            return None
            
        try:
            return await self.users.find_one({"user_id": user_id})
        except Exception as e:
            logger.error(f"❌ Error getting user from database: {e}")
            return None
    
    async def update_user_activity(self, user_id: int):
        """Update user's last activity"""
        if not self.enabled:
            return
            
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"❌ Error updating user activity: {e}")
    
    async def increment_user_downloads(self, user_id: int):
        """Increment user's download count"""
        if not self.enabled:
            return
            
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_downloads": 1}}
            )
        except Exception as e:
            logger.error(f"❌ Error incrementing download count: {e}")
    
    async def log_download(self, user_id: int, filename: str, file_size: int, url: str):
        """Log download to database"""
        if not self.enabled:
            return
            
        try:
            download_data = {
                "user_id": user_id,
                "filename": filename,
                "file_size": file_size,
                "url": url,
                "timestamp": datetime.utcnow(),
                "success": True
            }
            
            await self.downloads.insert_one(download_data)
            await self.increment_user_downloads(user_id)
            logger.info(f"📥 Download logged for user {user_id}: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error logging download: {e}")
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics"""
        if not self.enabled:
            return {"downloads": 0, "total_size": 0}
            
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_downloads": {"$sum": 1},
                    "total_size": {"$sum": "$file_size"}
                }}
            ]
            
            result = await self.downloads.aggregate(pipeline).to_list(1)
            
            if result:
                return {
                    "downloads": result[0]["total_downloads"],
                    "total_size": result[0]["total_size"]
                }
            else:
                return {"downloads": 0, "total_size": 0}
                
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return {"downloads": 0, "total_size": 0}
    
    async def get_total_users(self) -> int:
        """Get total number of users"""
        if not self.enabled:
            return 0
            
        try:
            return await self.users.count_documents({})
        except Exception as e:
            logger.error(f"❌ Error getting total users: {e}")
            return 0
    
    async def get_total_downloads(self) -> int:
        """Get total number of downloads"""
        if not self.enabled:
            return 0
            
        try:
            return await self.downloads.count_documents({})
        except Exception as e:
            logger.error(f"❌ Error getting total downloads: {e}")
            return 0

# Global database instance
db = Database()
