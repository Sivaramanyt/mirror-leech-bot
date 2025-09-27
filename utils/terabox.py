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
        self.chunk_size = 1024 * 1024  # 1MB chunks for faster download

    async def get_session(self):
        """Get or create aiohttp session with extended timeouts"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=8,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
            # Extended timeouts for large files
            timeout = aiohttp.ClientTimeout(
                total=1800,  # 30 minutes total
                connect=60,  # 1 minute connect
                sock_read=300  # 5 minutes read timeout per chunk
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": self.user_agent}
            )
        return self.session

    def is_supported_domain(self, url: str) -> bool:
        """Check if URL is from supported Terabox domains"""
        supported_domains = [
            "terabox.com", "nephobox.com", "4funbox.com", "mirrobox.com",
            "momerybox.com", "teraboxapp.com", "1024tera.com", "terabox.app",
            "gibibox.com", "goaibox.com", "terasharelink.com"
        ]
        return any(domain in url for domain in supported_domains)

    async def extract_file_info(self, url: str) -> dict:
        """Extract file information from Terabox URL using API"""
        try:
            logger.info(f"🔍 Extracting info from: {url[:50]}...")
            
            api_request_url = f"{self.api_url}?url={quote(url)}"
            session = await self.get_session()
            
            async with session.get(api_request_url) as response:
                logger.info(f"📊 API Response Status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API failed with status {response.status}")
                
                req = await response.json()
                
                if "✅ Status" not in req:
                    raise Exception("File not found in API response")
                
                if "📜 Extracted Info" not in req:
                    raise Exception("No extracted info in API response")
                
                extracted_info = req["📜 Extracted Info"]
                logger.info(f"📊 Found {len(extracted_info)} files")
                
                if extracted_info:
                    data = extracted_info[0]
                    filename = data.get("📂 Title", "terabox_file")
                    download_url = data.get("🔽 Direct Download Link", "")
                    
                    # Add extension if missing
                    if not os.path.splitext(filename)[1]:
                        filename += ".mp4"
                    
                    result = {
                        "success": True,
                        "filename": sanitize_filename(filename),
                        "download_url": download_url,
                        "title": filename
                    }
                    
                    logger.info(f"✅ File info extracted: {result['filename']}")
                    return result
                else:
                    raise Exception("No files in extracted info")
                    
        except Exception as e:
            logger.error(f"❌ Error extracting info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def download_file_with_retry(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None, max_retries: int = 3) -> Optional[str]:
        """Download file with retry logic and better error handling"""
        download_path = os.path.join("/tmp", filename)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📥 Download attempt {attempt + 1}/{max_retries}")
                session = await self.get_session()
                
                async with session.get(download_url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    logger.info(f"📦 Starting download: {filename} - {get_readable_file_size(total_size)}")
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback every 2MB
                            if progress_callback and total_size > 0 and downloaded % (2 * 1024 * 1024) < self.chunk_size:
                                try:
                                    await progress_callback(downloaded, total_size)
                                except Exception:
                                    pass  # Ignore progress errors
                    
                    # Verify download completed
                    if os.path.exists(download_path):
                        actual_size = os.path.getsize(download_path)
                        if total_size > 0 and actual_size < (total_size * 0.95):  # Allow 5% tolerance
                            raise Exception(f"Incomplete download: {actual_size}/{total_size} bytes")
                        
                        logger.info(f"✅ Download complete: {filename} ({get_readable_file_size(actual_size)})")
                        return download_path
                    else:
                        raise Exception("Download file not found after completion")
                        
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Download attempt {attempt + 1} failed: {error_msg}")
                
                # Clean up partial file
                try:
                    if os.path.exists(download_path):
                        os.remove(download_path)
                except:
                    pass
                
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"❌ All {max_retries} download attempts failed")
                    return None
                else:
                    # Wait before retry
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Download file from Terabox with enhanced error handling"""
        try:
            logger.info(f"🚀 Starting download: {url[:50]}...")
            
            if not self.is_supported_domain(url):
                raise Exception("Unsupported domain")
            
            # Get file info
            file_info = await self.extract_file_info(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "Failed to get file info"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            
            if not download_url:
                raise Exception("No download URL found")
            
            # Download with retry
            return await self.download_file_with_retry(download_url, filename, progress_callback)
                    
        except Exception as e:
            logger.error(f"❌ Download error: {e}")
            return None

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
                
