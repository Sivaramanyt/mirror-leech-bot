import asyncio
import logging
import os
from typing import Dict, Optional
import aiofiles
import json
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)

class VerificationSystem:
    def __init__(self):
        # Your exact configuration style
        self.SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "")
        self.SHORTLINK_API = os.environ.get("SHORTLINK_API", "")
        self.VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', 21600))  # 6 hours
        self.IS_VERIFY = os.environ.get("IS_VERIFY", "True")
        self.TUT_VID = os.environ.get("TUT_VID", "")
        self.FREE_DOWNLOAD_LIMIT = int(os.environ.get("FREE_DOWNLOAD_LIMIT", 3))
        
        # Storage files
        self.users_file = "/tmp/users.json"
        self.tokens_file = "/tmp/tokens.json"
        
    async def load_file(self, filename: str) -> Dict:
        """Load JSON file"""
        try:
            if os.path.exists(filename):
                async with aiofiles.open(filename, 'r') as f:
                    content = await f.read()
                    return json.loads(content) if content else {}
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
        return {}

    async def save_file(self, filename: str, data: Dict):
        """Save JSON file"""
        try:
            async with aiofiles.open(filename, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")

    async def get_user_downloads(self, user_id: int) -> int:
        """Get user download count"""
        users = await self.load_file(self.users_file)
        return users.get(str(user_id), {}).get("downloads", 0)

    async def increment_downloads(self, user_id: int) -> int:
        """Increment user downloads"""
        users = await self.load_file(self.users_file)
        user_key = str(user_id)
        
        if user_key not in users:
            users[user_key] = {"downloads": 0, "first_use": datetime.now().isoformat()}
        
        users[user_key]["downloads"] += 1
        users[user_key]["last_download"] = datetime.now().isoformat()
        await self.save_file(self.users_file, users)
        
        return users[user_key]["downloads"]

    def needs_verification(self, download_count: int) -> bool:
        """Check if verification is needed"""
        if self.IS_VERIFY.lower() != "true":
            return False
        return download_count >= self.FREE_DOWNLOAD_LIMIT

    async def create_token(self, user_id: int, url: str) -> str:
        """Create verification token"""
        import uuid
        token = str(uuid.uuid4())[:8]  # Short token
        
        tokens = await self.load_file(self.tokens_file)
        tokens[token] = {
            "user_id": user_id,
            "url": url,
            "created": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(seconds=self.VERIFY_EXPIRE)).isoformat(),
            "used": False
        }
        await self.save_file(self.tokens_file, tokens)
        
        logger.info(f"🔐 Token created: {token} for user {user_id}")
        return token

    async def generate_shortlink(self, token: str) -> str:
        """Generate shortlink"""
        if not self.SHORTLINK_URL:
            return f"https://example.com/verify?token={token}"
        
        verify_url = f"{self.SHORTLINK_URL}/verify?token={token}"
        
        if self.SHORTLINK_API:
            try:
                async with aiohttp.ClientSession() as session:
                    api_url = f"{self.SHORTLINK_API}{verify_url}"
                    async with session.get(api_url) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get('shortenedUrl', result.get('short_url', verify_url))
            except Exception as e:
                logger.error(f"Shortlink API error: {e}")
        
        return verify_url

    async def verify_token(self, token: str, user_id: int) -> Dict:
        """Verify token"""
        tokens = await self.load_file(self.tokens_file)
        
        if token not in tokens:
            return {"success": False, "error": "Invalid token"}
        
        token_data = tokens[token]
        
        if token_data["user_id"] != user_id:
            return {"success": False, "error": "Token not yours"}
        
        if token_data["used"]:
            return {"success": False, "error": "Token already used"}
        
        if datetime.now() > datetime.fromisoformat(token_data["expires"]):
            return {"success": False, "error": "Token expired"}
        
        # Mark as used
        tokens[token]["used"] = True
        await self.save_file(self.tokens_file, tokens)
        
        return {"success": True, "url": token_data["url"]}

    def format_time(self) -> str:
        """Format expire time"""
        hours = self.VERIFY_EXPIRE // 3600
        if hours > 0:
            return f"{hours} hours"
        else:
            return f"{self.VERIFY_EXPIRE // 60} minutes"

# Global instance
verification = VerificationSystem()
        
