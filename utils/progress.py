import asyncio
import logging

logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self):
        self.active_tasks = {}
    
    async def create_progress_task(self, task_id, message):
        """Create a progress tracking task"""
        self.active_tasks[task_id] = {
            "message": message,
            "status": "starting",
            "progress": 0
        }
        logger.info(f"Progress task created: {task_id}")
    
    async def update_progress(self, task_id, downloaded, total):
        """Update download progress"""
        if task_id not in self.active_tasks:
            return
        
        try:
            progress = (downloaded / total) * 100 if total > 0 else 0
            self.active_tasks[task_id]["progress"] = progress
            
            # Update every 5% to avoid spam
            if progress % 5 < 1:
                message = self.active_tasks[task_id]["message"]
                await message.edit_text(
                    f"📥 **Downloading...**\n\n"
                    f"📊 **Progress:** {progress:.1f}%\n"
                    f"📦 **Downloaded:** {downloaded / (1024*1024):.1f} MB\n"
                    f"📋 **Total:** {total / (1024*1024):.1f} MB\n"
                    f"⚡ **Status:** Lightning-fast download"
                )
        except Exception as e:
            logger.error(f"Progress update error: {e}")
    
    async def complete_task(self, task_id):
        """Mark task as completed"""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
            logger.info(f"Progress task completed: {task_id}")
