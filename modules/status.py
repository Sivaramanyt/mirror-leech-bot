import asyncio
import logging
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.helpers import format_task_info, get_readable_time
import time

logger = logging.getLogger(__name__)

class StatusHandler:
    def __init__(self, bot):
        self.bot = bot

    async def status_command(self, client: Client, message: Message):
        """Handle /status command"""
        try:
            active_tasks = self.bot.active_tasks

            if not active_tasks:
                await message.reply_text("📊 **No active downloads**")
                return

            # Format status message
            status_text = "📊 **Active Downloads:**\n\n"

            for task_id, task_info in list(active_tasks.items())[:10]:  # Show max 10 tasks
                task_text = format_task_info(task_info)
                status_text += f"**ID:** `{task_id}`\n{task_text}\n\n"

            if len(active_tasks) > 10:
                status_text += f"... and {len(active_tasks) - 10} more tasks"

            # Add action buttons
            buttons = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="status_refresh")],
                [InlineKeyboardButton("❌ Cancel All", callback_data="cancel_all")]
            ]

            await message.reply_text(
                status_text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logger.error(f"Status command error: {e}")
            await message.reply_text("❌ **Error getting status**")

    async def get_system_status(self) -> str:
        """Get system status information"""
        try:
            import psutil

            # Get system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get bot uptime
            uptime = get_readable_time(int(time.time() - getattr(self.bot, 'start_time', time.time())))

            status = f"""
🖥️ **System Status:**

**CPU Usage:** {cpu_percent}%
**RAM Usage:** {memory.percent}% ({memory.used // (1024**3)} GB / {memory.total // (1024**3)} GB)
**Disk Usage:** {disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)

⏱️ **Uptime:** {uptime}
📊 **Active Tasks:** {len(self.bot.active_tasks)}

🔗 **Database:** {'✅ Connected' if self.bot.database else '❌ Not connected'}
☁️ **GDrive:** {'✅ Enabled' if self.bot.gdrive_handler else '❌ Disabled'}
            """.strip()

            return status

        except ImportError:
            # psutil not available
            return f"""
📊 **Bot Status:**

⏱️ **Active Tasks:** {len(self.bot.active_tasks)}
🔗 **Database:** {'✅ Connected' if self.bot.database else '❌ Not connected'}
☁️ **GDrive:** {'✅ Enabled' if self.bot.gdrive_handler else '❌ Disabled'}
            """.strip()
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return "❌ **Error getting system status**"
