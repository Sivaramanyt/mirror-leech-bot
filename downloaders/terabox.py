import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
from utils.helpers import sanitize_filename, get_readable_file_size
import aiofiles

logger = logging.getLogger(__name__)

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
        self.chunk_size = 128 * 1024  # 128KB chunks (16x larger!)
    
    async def get_session(self):
        """Get or create optimized aiohttp session - COMPATIBLE VERSION"""
        if not self.session:
            # COMPATIBLE TCPConnector settings (removed tcp_nodelay)
            connector = aiohttp.TCPConnector(
                limit=15,           # Total connection pool size
                limit_per_host=6,   # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                enable_cleanup_closed=True
                # REMOVED: tcp_nodelay (not supported in aiohttp 3.9.1)
            )
            
            timeout = aiohttp.ClientTimeout(
                total=600,      # 10 minutes total
                connect=30,     # 30s to connect  
                sock_read=120   # 2 minutes read timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Keep-Alive": "timeout=5, max=1000"
                }
            )
        return self.session
    
    def is_supported_domain(self, url: str) -> bool:
        """Check if URL is from supported Terabox domains"""
        supported_domains = [
            "terabox.com", "nephobox.com", "4funbox.com", "mirrobox.com",
            "momerybox.com", "teraboxapp.com", "1024tera.com", "terabox.app",
            "gibibox.com", "goaibox.com", "terasharelink.com", "teraboxlink.com",
            "freeterabox.com", "1024terabox.com", "teraboxshare.com", 
            "terafileshare.com", "terabox.club"
        ]
        return any(domain in url for domain in supported_domains)
    
    async def extract_file_info(self, url: str) -> dict:
        """Extract file information from Terabox URL using official API"""
        try:
            logger.info(f"🔍 Extracting info from URL: {url}")
            
            if "/file/" in url:
                logger.info("Direct file link detected")
                return {"single_url": url, "filename": "terabox_file.mp4"}
            
            api_request_url = f"{self.api_url}?url={quote(url)}"
            logger.info(f"📡 Calling API: {api_request_url}")
            
            session = await self.get_session()
            
            async with session.get(api_request_url) as response:
                logger.info(f"📊 API Response Status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ API request failed with status {response.status}: {error_text}")
                    raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                response_text = await response.text()
                logger.info(f"📋 API Response (first 200 chars): {response_text[:200]}...")
                
                req = await response.json()
                logger.info(f"🔍 API JSON keys: {list(req.keys())}")
            
            if "✅ Status" not in req:
                raise Exception(f"File not found in API response! API returned: {req}")
            
            if "📜 Extracted Info" not in req:
                raise Exception(f"No extracted info in API response! API returned: {req}")
                
            extracted_info = req["📜 Extracted Info"]
            logger.info(f"📊 Found {len(extracted_info)} files in API response")
            
            details = {"contents": [], "title": "", "total_size": 0}
            
            for i, data in enumerate(extracted_info):
                logger.info(f"🔍 Processing file {i+1}: {data.get('📂 Title', 'Unknown')}")
                
                original_filename = data.get("📂 Title", f"terabox_file_{i}")
                
                if not self.has_video_extension(original_filename):
                    original_filename += ".mp4"
                
                item = {
                    "path": "",
                    "filename": sanitize_filename(original_filename),
                    "url": data.get("🔽 Direct Download Link", ""),
                }
                details["contents"].append(item)
                logger.info(f"✅ Added file: {item['filename']} -> {item['url'][:50]}...")
            
            details["title"] = extracted_info[0].get("📂 Title", "Unknown")
            
            if len(details["contents"]) == 1:
                result = {
                    "single_url": details["contents"][0]["url"],
                    "filename": details["contents"][0]["filename"],
                    "title": details["title"]
                }
                logger.info(f"✅ Single file result: {result['filename']}")
                return result
            
            logger.info(f"✅ Multiple files result: {len(details['contents'])} files")
            return details
            
        except Exception as e:
            logger.error(f"❌ Error extracting Terabox info: {str(e)}")
            raise Exception(f"Terabox API error: {str(e)}")
    
    def has_video_extension(self, filename: str) -> bool:
        """Check if filename has video extension"""
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        ext = os.path.splitext(filename.lower())[1]
        return ext in video_extensions
    
    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """High-speed download - COMPATIBLE VERSION"""
        try:
            logger.info(f"🚀 Starting HIGH-SPEED Terabox download: {url}")
            
            file_info = await self.extract_file_info(url)
            
            if "single_url" in file_info:
                download_url = file_info["single_url"]
                filename = file_info["filename"]
            else:
                if not file_info["contents"]:
                    raise Exception("No files found")
                download_url = file_info["contents"][0]["url"]
                filename = file_info["contents"][0]["filename"]
            
            if not os.path.splitext(filename)[1]:
                filename += '.mp4'
            
            download_path = os.path.join('/tmp', filename)
            
            # OPTIMIZED single connection download
            session = await self.get_session()
            logger.info(f"🚀 Starting OPTIMIZED high-speed download")
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    logger.info(f"📦 File size: {get_readable_file_size(total_size)}")
                    logger.info(f"⚡ Using {self.chunk_size // 1024}KB chunks for high speed")
                    
                    # Large buffer for maximum efficiency
                    buffer_size = 512 * 1024  # 512KB buffer
                    buffer_data = bytearray()
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            buffer_data.extend(chunk)
                            downloaded += len(chunk)
                            
                            # Write buffer when full for efficiency
                            if len(buffer_data) >= buffer_size:
                                await f.write(buffer_data)
                                buffer_data.clear()
                            
                            # Progress callback
                            if progress_callback and total_size > 0:
                                try:
                                    await progress_callback(downloaded, total_size, task_id)
                                except:
                                    pass
                        
                        # Write remaining buffer
                        if buffer_data:
                            await f.write(buffer_data)
                    
                    logger.info(f"✅ OPTIMIZED download complete: {get_readable_file_size(downloaded)}")
                    return download_path
                else:
                    raise Exception(f"Download failed: HTTP {response.status}")
                
        except Exception as e:
            logger.error(f"❌ Download error: {e}")
            raise e
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
            
