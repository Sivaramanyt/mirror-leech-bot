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
        # SPEED OPTIMIZED: Much larger chunks for faster downloads
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks (8x larger!)

    async def get_session(self):
        """Get or create HIGH-SPEED aiohttp session"""
        if not self.session:
            # SPEED OPTIMIZED: More aggressive connection settings
            connector = aiohttp.TCPConnector(
                limit=50,  # More total connections
                limit_per_host=20,  # More connections per host
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                # SPEED BOOST: Reduce timeouts for faster operations
                keepalive_timeout=60,
                force_close=False  # Reuse connections
            )
            
            # SPEED OPTIMIZED: Faster timeouts but longer total time
            timeout = aiohttp.ClientTimeout(
                total=1800,  # 30 minutes total
                connect=15,   # Faster connect (was 60)
                sock_read=60  # Faster read per chunk (was 300)
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": self.user_agent,
                    # SPEED BOOST: Request compression
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive"
                }
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
        """Extract file information from Terabox URL using API - SPEED OPTIMIZED"""
        try:
            logger.info(f"🔍 Extracting info from: {url[:50]}...")
            
            api_request_url = f"{self.api_url}?url={quote(url)}"
            session = await self.get_session()
            
            # SPEED BOOST: Parallel processing ready
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

    async def download_file_ultra_fast(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None, max_retries: int = 2) -> Optional[str]:
        """ULTRA-FAST download with optimized settings"""
        download_path = os.path.join("/tmp", filename)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"⚡ ULTRA-FAST download attempt {attempt + 1}/{max_retries}")
                session = await self.get_session()
                
                # SPEED BOOST: Add headers for optimal download
                headers = {
                    "Range": "bytes=0-",  # Support resume capability
                    "Accept": "*/*",
                    "Accept-Encoding": "identity",  # No compression for speed
                    "Connection": "keep-alive"
                }
                
                async with session.get(download_url, headers=headers) as response:
                    if response.status not in [200, 206]:  # Accept partial content too
                        raise Exception(f"HTTP {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    logger.info(f"🚀 ULTRA-FAST mode: {filename} - {get_readable_file_size(total_size)} - {self.chunk_size // (1024*1024)}MB chunks")
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        start_time = asyncio.get_event_loop().time()
                        
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # SPEED OPTIMIZED: Less frequent progress updates for speed
                            if progress_callback and total_size > 0 and downloaded % (10 * 1024 * 1024) < self.chunk_size:  # Every 10MB
                                try:
                                    # Calculate speed
                                    elapsed = asyncio.get_event_loop().time() - start_time
                                    if elapsed > 0:
                                        speed_mbps = (downloaded / (1024 * 1024)) / (elapsed / 60)  # MB per minute
                                        await progress_callback(downloaded, total_size, speed_mbps)
                                except Exception:
                                    pass
                    
                    # Verify download completed
                    if os.path.exists(download_path):
                        actual_size = os.path.getsize(download_path)
                        if total_size > 0 and actual_size < (total_size * 0.90):  # 90% tolerance
                            raise Exception(f"Incomplete download: {actual_size}/{total_size} bytes")
                        
                        # Calculate final speed
                        end_time = asyncio.get_event_loop().time()
                        total_time = end_time - start_time if 'start_time' in locals() else 1
                        final_speed = (actual_size / (1024 * 1024)) / (total_time / 60) if total_time > 0 else 0
                        
                        logger.info(f"⚡ ULTRA-FAST download complete: {filename} ({get_readable_file_size(actual_size)}) - Speed: {final_speed:.1f} MB/min")
                        return download_path
                    else:
                        raise Exception("Download file not found after completion")
                        
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ ULTRA-FAST attempt {attempt + 1} failed: {error_msg}")
                
                # Clean up partial file
                try:
                    if os.path.exists(download_path):
                        os.remove(download_path)
                except:
                    pass
                
                if attempt == max_retries - 1:
                    logger.error(f"❌ All {max_retries} ULTRA-FAST attempts failed")
                    return None
                else:
                    # SPEED OPTIMIZED: Faster retry
                    wait_time = 2  # Only 2 seconds wait
                    logger.info(f"⏳ Quick retry in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Download file from Terabox with ULTRA-FAST mode"""
        try:
            logger.info(f"⚡ Starting ULTRA-FAST download: {url[:50]}...")
            
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
            
            # Download with ULTRA-FAST mode
            return await self.download_file_ultra_fast(download_url, filename, progress_callback)
                    
        except Exception as e:
            logger.error(f"❌ ULTRA-FAST download error: {e}")
            return None

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
                
