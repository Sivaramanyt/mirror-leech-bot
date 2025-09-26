import logging
from pyrogram import Client
from pyrogram.types import Message
import config

logger = logging.getLogger(__name__)

class AuthHandler:
    def __init__(self, bot):
        self.bot = bot

    async def auth_command(self, client: Client, message: Message):
        """Handle /auth command - Owner only"""
        if message.from_user.id != config.OWNER_ID:
            await message.reply_text("❌ **Only owner can authorize users**")
            return

        args = message.text.split()

        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:** `/auth [user_id]`\n\n"
                "**Example:** `/auth 123456789`"
            )
            return

        try:
            user_id = int(args[1])

            # Add to database if available
            if self.bot.database:
                user_data = {
                    'user_id': user_id,
                    'authorized': True,
                    'authorized_by': message.from_user.id,
                    'authorized_at': message.date
                }

                success = await self.bot.database.add_user(user_id, user_data)

                if success:
                    await message.reply_text(f"✅ **User {user_id} authorized successfully**")
                else:
                    await message.reply_text("❌ **Failed to authorize user**")
            else:
                await message.reply_text(
                    f"✅ **User {user_id} authorized**\n"
                    "⚠️ **Note:** Database not configured, authorization is temporary"
                )

        except ValueError:
            await message.reply_text("❌ **Invalid user ID**")
        except Exception as e:
            logger.error(f"Auth command error: {e}")
            await message.reply_text("❌ **Error authorizing user**")

    async def unauth_command(self, client: Client, message: Message):
        """Handle /unauth command - Owner only"""
        if message.from_user.id != config.OWNER_ID:
            await message.reply_text("❌ **Only owner can unauthorize users**")
            return

        args = message.text.split()

        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:** `/unauth [user_id]`\n\n"
                "**Example:** `/unauth 123456789`"
            )
            return

        try:
            user_id = int(args[1])

            if user_id == config.OWNER_ID:
                await message.reply_text("❌ **Cannot unauthorize owner**")
                return

            # Remove from database if available
            if self.bot.database:
                success = await self.bot.database.delete_user(user_id)

                if success:
                    await message.reply_text(f"✅ **User {user_id} unauthorized successfully**")
                else:
                    await message.reply_text("❌ **User not found or error occurred**")
            else:
                await message.reply_text(
                    f"✅ **User {user_id} unauthorized**\n"
                    "⚠️ **Note:** Database not configured, change is temporary"
                )

        except ValueError:
            await message.reply_text("❌ **Invalid user ID**")
        except Exception as e:
            logger.error(f"Unauth command error: {e}")
            await message.reply_text("❌ **Error unauthorizing user**")

    async def users_command(self, client: Client, message: Message):
        """Handle /users command - Sudo users only"""
        if message.from_user.id not in config.SUDO_USERS_LIST:
            await message.reply_text("❌ **You don't have permission to view users**")
            return

        try:
            if self.bot.database:
                users = await self.bot.database.get_all_users()

                if not users:
                    await message.reply_text("📝 **No authorized users found**")
                    return

                users_text = "👥 **Authorized Users:**\n\n"

                for i, user in enumerate(users[:20], 1):  # Show max 20 users
                    user_id = user.get('user_id')
                    authorized_at = user.get('authorized_at', 'Unknown')

                    users_text += f"**{i}.** `{user_id}`"
                    if authorized_at != 'Unknown':
                        users_text += f" - {authorized_at.strftime('%Y-%m-%d')}"
                    users_text += "\n"

                if len(users) > 20:
                    users_text += f"\n... and {len(users) - 20} more users"

                await message.reply_text(users_text)

            else:
                config_users = config.SUDO_USERS_LIST + config.AUTHORIZED_CHATS_LIST

                if not config_users:
                    await message.reply_text("📝 **No users configured**")
                    return

                users_text = "👥 **Configured Users:**\n\n"

                for i, user_id in enumerate(config_users, 1):
                    users_text += f"**{i}.** `{user_id}`\n"

                users_text += "\n⚠️ **Note:** Database not configured"
                await message.reply_text(users_text)

        except Exception as e:
            logger.error(f"Users command error: {e}")
            await message.reply_text("❌ **Error getting users list**")

    async def is_authorized(self, user_id: int, chat_id: int) -> bool:
        """Check if user is authorized"""
        # Owner is always authorized
        if user_id == config.OWNER_ID:
            return True

        # Check sudo users
        if user_id in config.SUDO_USERS_LIST:
            return True

        # Check authorized chats
        if config.AUTHORIZED_CHATS_LIST and chat_id in config.AUTHORIZED_CHATS_LIST:
            return True

        # Check database if available
        if self.bot.database:
            user_data = await self.bot.database.get_user(user_id)
            if user_data and user_data.get('authorized', False):
                return True

        # If no restrictions set, allow all
        if not config.AUTHORIZED_CHATS_LIST and not config.SUDO_USERS_LIST:
            return True

        return False
