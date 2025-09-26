import asyncio
import logging
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            # Test connection
            await self.client.admin.command('ping')
            self.db = self.client.mirror_leech_bot
            logger.info("✅ Database connected successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("✅ Database connection closed")

    # User management
    async def add_user(self, user_id: int, user_data: Dict[str, Any]):
        """Add or update user in database"""
        try:
            await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user from database"""
        try:
            user = await self.db.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    async def delete_user(self, user_id: int) -> bool:
        """Delete user from database"""
        try:
            result = await self.db.users.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    async def get_all_users(self) -> list:
        """Get all users from database"""
        try:
            users = []
            async for user in self.db.users.find():
                users.append(user)
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    # Task management
    async def add_task(self, task_id: str, task_data: Dict[str, Any]):
        """Add task to database"""
        try:
            await self.db.tasks.insert_one({
                "task_id": task_id,
                **task_data
            })
            return True
        except Exception as e:
            logger.error(f"Error adding task {task_id}: {e}")
            return False

    async def update_task(self, task_id: str, update_data: Dict[str, Any]):
        """Update task in database"""
        try:
            await self.db.tasks.update_one(
                {"task_id": task_id},
                {"$set": update_data}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task from database"""
        try:
            task = await self.db.tasks.find_one({"task_id": task_id})
            return task
        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return None

    async def delete_task(self, task_id: str) -> bool:
        """Delete task from database"""
        try:
            result = await self.db.tasks.delete_one({"task_id": task_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False

    async def get_active_tasks(self, user_id: Optional[int] = None) -> list:
        """Get active tasks"""
        try:
            query = {"status": {"$in": ["downloading", "uploading", "queued"]}}
            if user_id:
                query["user_id"] = user_id

            tasks = []
            async for task in self.db.tasks.find(query):
                tasks.append(task)
            return tasks
        except Exception as e:
            logger.error(f"Error getting active tasks: {e}")
            return []

    # Settings management
    async def update_settings(self, key: str, value: Any):
        """Update bot settings"""
        try:
            await self.db.settings.update_one(
                {"key": key},
                {"$set": {"value": value}},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False

    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get bot setting"""
        try:
            setting = await self.db.settings.find_one({"key": key})
            return setting["value"] if setting else default
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return default
