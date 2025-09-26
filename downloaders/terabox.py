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
        self.chunk_size = 128 * 1024  # 128KB chunks for speed
    
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
    
    def parse_file_size(self, size_str: str) -> int:
        """Parse file size string to bytes"""
        size_str = size_str.upper().replace(" ", "")
        
        if "KB" in size_str:
            return int(float(size_str.replace("KB", "")) * 1024)
        elif "MB" in size_str:
            return int(float(size_str.replace("MB", "")) * 1024 * 1024)
        elif "GB" in size_str:
            return int(float(size_str.replace("GB", "")) * 1024 * 1024 * 1024)
        elif "TB" in size_str:
            return int(float(size_str.replace("TB", "")) * 1024 * 1024 * 1024 * 1024)
        else:
            return int(size_str.replace("B", "")) if size_str.replace("B", "").isdigit() else 0
    
    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """🛡️ NETWORK RESILIENT HIGH-SPEED DOWNLOAD with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"🚀 Starting HIGH-SPEED Terabox download (attempt {retry_count + 1}): {url}")
                
                # Validate URL
                if not self.is_supported_domain(url):
                    raise Exception("Unsupported Terabox domain")
                
                # Get file information using official API method
                file_info = await self.extract_file_info(url)
                logger.info(f"📋 File info extracted: {file_info}")
                
                if "single_url" in file_info:
                    # Single file download
                    download_url = file_info["single_url"]
                    filename = file_info["filename"]
                    logger.info(f"📥 Single file download: {filename}")
                else:
                    # Multiple files - download first one for now
                    if not file_info["contents"]:
                        raise Exception("No files found in folder")
                    
                    download_url = file_info["contents"][0]["url"]
                    filename = file_info["contents"][0]["filename"]
                    logger.info(f"📥 Multiple files, downloading first: {filename}")
                
                if not download_url:
                    raise Exception("No download URL found in API response")
                    
                # Ensure filename has extension
                if not os.path.splitext(filename)[1]:
                    filename += '.mp4'
                
                # Create download path
                download_path = os.path.join('/tmp', filename)
                logger.info(f"💾 Download path: {download_path}")
                
                # 🛡️ RESILIENT download with adaptive chunk size
                session = await self.get_session()
                logger.info(f"🛡️ Starting RESILIENT high-speed download (attempt {retry_count + 1})")
                
                # Use smaller chunks on retry for better network reliability
                reliable_chunk_size = 64 * 1024 if retry_count > 0 else self.chunk_size  # 64KB on retry
                
                async with session.get(download_url) as response:
                    logger.info(f"📊 Download response status: {response.status}")
                    
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        logger.info(f"📦 File size: {get_readable_file_size(total_size)}")
                        logger.info(f"⚡ Using {reliable_chunk_size // 1024}KB chunks (attempt {retry_count + 1})")
                        
                        # Smaller buffer for better reliability
                        buffer_size = 256 * 1024  # 256KB buffer
                        buffer_data = bytearray()
                        last_progress = 0
                        
                        async with aiofiles.open(download_path, 'wb') as f:
                            try:
                                async for chunk in response.content.iter_chunked(reliable_chunk_size):
                                    if not chunk:  # Empty chunk indicates end
                                        break
                                        
                                    buffer_data.extend(chunk)
                                    downloaded += len(chunk)
                                    
                                    # Write buffer when full for efficiency
                                    if len(buffer_data) >= buffer_size:
                                        await f.write(buffer_data)
                                        buffer_data.clear()
                                    
                                    # Progress callback - less frequent on retries to avoid flood wait
                                    progress_interval = 2048 * 1024 if retry_count == 0 else 4096 * 1024  # 2MB or 4MB intervals
                                    if downloaded - last_progress >= progress_interval:
                                        if progress_callback and total_size > 0:
                                            try:
                                                await progress_callback(downloaded, total_size, task_id)
                                                last_progress = downloaded
                                            except Exception as pe:
                                                logger.warning(f"Progress callback error: {pe}")
                                
                                # Write remaining buffer
                                if buffer_data:
                                    await f.write(buffer_data)
                                    
                            except Exception as chunk_error:
                                logger.error(f"❌ Chunk download error: {chunk_error}")
                                raise chunk_error
                        
                        # Verify download completion
                        actual_size = os.path.getsize(download_path)
                        if actual_size == total_size:
                            logger.info(f"✅ RESILIENT download complete: {get_readable_file_size(downloaded)}")
                            return download_path
                        else:
                            logger.warning(f"⚠️ Size mismatch: expected {total_size}, got {actual_size}")
                            if retry_count < max_retries - 1:
                                logger.info(f"🔄 Retrying with smaller chunks...")
                                retry_count += 1
                                await asyncio.sleep(3)  # Wait before retry
                                continue
                            else:
                                logger.info(f"✅ Returning partial download: {get_readable_file_size(actual_size)}")
                                return download_path  # Return partial download
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Download failed: HTTP {response.status} - {error_text}")
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            logger.info(f"🔄 HTTP Error - Retrying in 5 seconds... (attempt {retry_count + 1}/{max_retries})")
                            await asyncio.sleep(5)
                            continue
                        else:
                            raise Exception(f"Download failed: HTTP {response.status} - {error_text}")
                            
            except asyncio.TimeoutError as e:
                if retry_count < max_retries - 1:
                    retry_count += 1
                    wait_time = min(10 * retry_count, 30)  # Progressive wait: 10s, 20s, 30s
                    logger.warning(f"⏰ Download timeout, retrying in {wait_time}s... (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Final timeout after {max_retries} attempts: {str(e)}")
                    raise Exception(f"Download timeout after {max_retries} attempts: {str(e)}")
                    
            except Exception as e:
                error_msg = str(e)
                # Special handling for network payload errors
                if any(keyword in error_msg.lower() for keyword in ["payload", "completed", "connection", "reset"]):
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        wait_time = 5 * retry_count
                        logger.warning(f"🌐 Network payload error, retrying with smaller chunks in {wait_time}s... (attempt {retry_count + 1}/{max_retries}): {error_msg}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Network error after {max_retries} attempts: {error_msg}")
                        raise Exception(f"Network download failed after {max_retries} attempts: {error_msg}")
                else:
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        logger.warning(f"❌ Download error, retrying in 5 seconds... (attempt {retry_count + 1}/{max_retries}): {error_msg}")
                        await asyncio.sleep(5)
                        continue
                    else:
                        logger.error(f"❌ Terabox download error: {error_msg}")
                        logger.error(f"❌ Error type: {type(e).__name__}")
                        raise Exception(f"Download failed: {error_msg}")
        
        raise Exception("Download failed after maximum retries")
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
                
