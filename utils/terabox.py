import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
import aiofiles

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """Simple filename sanitization"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:250]

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
        # MAXIMUM SPEED: Large chunks
        self.chunk_size = 16 * 1024 * 1024  # 16MB chunks

    async def get_session(self):
        """Get HIGH-PERFORMANCE session with redirect handling"""
        if not self.session:
            # MAXIMUM PERFORMANCE: Allow redirects and more connections
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=50,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                keepalive_timeout=120,
                force_close=False
            )
            
            # SPEED OPTIMIZED: Fast timeouts
            timeout = aiohttp.ClientTimeout(
                total=1800,  # 30 minutes
                connect=10,   # Fast connect
                sock_read=60  # Fast read
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                # CRITICAL FIX: Allow redirects automatically
                connector_owner=True,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "*/*",
                    "Accept-Encoding": "identity",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache"
                }
            )
        return self.session

    async def extract_file_info(self, url: str) -> dict:
        """Extract file information - MAXIMUM SPEED"""
        try:
            logger.info(f"🚀 MAXIMUM SPEED extraction: {url[:50]}...")
            
            api_request_url = f"{self.api_url}?url={quote(url)}"
            session = await self.get_session()
            
            async with session.get(api_request_url) as response:
                if response.status != 200:
                    raise Exception(f"API failed: {response.status}")
                
                req = await response.json()
                
                if "✅ Status" not in req or "📜 Extracted Info" not in req:
                    raise Exception("Invalid API response")
                
                extracted_info = req["📜 Extracted Info"]
                if not extracted_info:
                    raise Exception("No files found")
                
                data = extracted_info[0]
                filename = data.get("📂 Title", "terabox_file")
                download_url = data.get("🔽 Direct Download Link", "")
                
                if not os.path.splitext(filename)[1]:
                    filename += ".mp4"
                
                logger.info(f"🚀 MAXIMUM SPEED file found: {filename}")
                return {
                    "success": True,
                    "filename": sanitize_filename(filename),
                    "download_url": download_url,
                    "title": filename
                }
                    
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            return {"success": False, "error": str(e)}

    async def download_file_ultra_fast_v2(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """ULTRA-FAST download with redirect handling - VERSION 2"""
        download_path = os.path.join("/tmp", filename)
        
        try:
            session = await self.get_session()
            
            logger.info(f"🚀 ULTRA-FAST V2 download: {filename}")
            
            # FIXED: Use GET instead of HEAD to avoid 302 issues
            # Start download and get headers
            async with session.get(download_url) as response:
                # CRITICAL FIX: Follow redirects automatically
                if response.status not in [200, 206]:
                    logger.error(f"❌ Download failed: HTTP {response.status}")
                    raise Exception(f"Download failed: HTTP {response.status}")
                
                # Get file size from headers
                total_size = int(response.headers.get('content-length', 0))
                if total_size == 0:
                    logger.warning("⚠️ Cannot determine file size, proceeding anyway...")
                    total_size = 50 * 1024 * 1024  # Assume 50MB if unknown
                
                logger.info(f"🚀 ULTRA-FAST V2 mode: {filename}")
                logger.info(f"📦 Size: {get_readable_file_size(total_size)}")
                logger.info(f"⚡ Using 16MB chunks for maximum speed")
                
                downloaded = 0
                start_time = asyncio.get_event_loop().time()
                
                # ULTRA-FAST download with large chunks
                async with aiofiles.open(download_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        if not chunk:
                            break
                        
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress every 32MB for speed
                        if progress_callback and downloaded % (32 * 1024 * 1024) < self.chunk_size:
                            try:
                                elapsed = asyncio.get_event_loop().time() - start_time
                                speed_mbps = (downloaded / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                                await progress_callback(downloaded, max(total_size, downloaded), speed_mbps)
                            except:
                                pass
                
                # Verify file exists
                if not os.path.exists(download_path):
                    raise Exception("Download file not created")
                
                actual_size = os.path.getsize(download_path)
                elapsed = asyncio.get_event_loop().time() - start_time
                final_speed = (actual_size / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                
                logger.info(f"🚀 ULTRA-FAST V2 complete: {filename} ({get_readable_file_size(actual_size)}) - Speed: {final_speed:.1f} MB/min")
                return download_path
                    
        except Exception as e:
            logger.error(f"❌ ULTRA-FAST V2 download error: {e}")
            # Clean up partial file
            try:
                if os.path.exists(download_path):
                    os.remove(download_path)
            except:
                pass
            return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """ULTRA-FAST download entry point - VERSION 2"""
        try:
            logger.info(f"🚀 ULTRA-FAST V2 download starting: {url[:50]}...")
            
            # Get file info
            file_info = await self.extract_file_info(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "File info failed"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            
            if not download_url:
                raise Exception("No download URL")
            
            # ULTRA-FAST V2 download with redirect handling
            result = await self.download_file_ultra_fast_v2(download_url, filename, progress_callback)
            return result
                    
        except Exception as e:
            logger.error(f"❌ ULTRA-FAST V2 download error: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
                
