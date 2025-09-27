import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote, urlparse
import aiofiles
import random

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
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks
        
        # BYPASS 403: Comprehensive headers for different scenarios
        self.browser_headers = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "cross-site",
                "Cache-Control": "max-age=0"
            },
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        ]

    async def get_session(self):
        """Get session with 403-bypass configuration"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                keepalive_timeout=60,
                force_close=False
            )
            
            timeout = aiohttp.ClientTimeout(
                total=1200,  # 20 minutes
                connect=30,   
                sock_read=120  
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self.session

    async def extract_file_info(self, url: str) -> dict:
        """Extract file information"""
        try:
            logger.info(f"🔍 Extracting info: {url[:50]}...")
            
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
                
                logger.info(f"✅ File found: {filename}")
                logger.info(f"🔗 Download URL: {download_url[:80]}...")
                
                return {
                    "success": True,
                    "filename": sanitize_filename(filename),
                    "download_url": download_url,
                    "title": filename,
                    "original_url": url
                }
                    
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            return {"success": False, "error": str(e)}

    async def download_bypass_403(self, download_url: str, filename: str, original_url: str, progress_callback: Optional[Callable] = None, max_retries: int = 5) -> Optional[str]:
        """BYPASS 403 with multiple header strategies"""
        download_path = os.path.join("/tmp", filename)
        
        for attempt in range(max_retries):
            try:
                # Fresh session for each attempt
                if self.session:
                    await self.session.close()
                    self.session = None
                
                session = await self.get_session()
                
                # BYPASS STRATEGY: Different headers per attempt
                headers = self.browser_headers[attempt % len(self.browser_headers)].copy()
                
                # BYPASS 403: Add specific headers based on URL
                parsed_url = urlparse(download_url)
                domain = parsed_url.netloc
                
                # Add domain-specific headers
                if 'terabox' in domain or '1024tera' in domain:
                    headers.update({
                        "Referer": original_url,
                        "Origin": f"https://{urlparse(original_url).netloc}",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "same-site"
                    })
                
                # BYPASS 403: Add random elements
                headers.update({
                    "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "X-Requested-With": "XMLHttpRequest" if attempt > 2 else None
                })
                
                # Remove None values
                headers = {k: v for k, v in headers.items() if v is not None}
                
                logger.info(f"🚀 BYPASS 403 attempt {attempt + 1}/{max_retries}: {filename}")
                logger.info(f"🔧 Using strategy: {headers.get('User-Agent', 'Unknown')[:50]}...")
                
                if attempt > 0:
                    delay = random.uniform(2, 5)
                    await asyncio.sleep(delay)
                
                async with session.get(download_url, headers=headers) as response:
                    logger.info(f"📊 Response Status: {response.status}")
                    logger.info(f"📋 Response Headers: {dict(list(response.headers.items())[:3])}")
                    
                    if response.status == 403:
                        logger.error(f"❌ 403 Forbidden with strategy {attempt + 1}")
                        continue
                    
                    if response.status not in [200, 206]:
                        raise Exception(f"HTTP {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    logger.info(f"✅ SUCCESS! Breaking through 403 barrier!")
                    logger.info(f"📦 Size: {get_readable_file_size(total_size)}")
                    
                    downloaded = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress every 16MB
                            if progress_callback and downloaded % (16 * 1024 * 1024) < self.chunk_size:
                                try:
                                    elapsed = asyncio.get_event_loop().time() - start_time
                                    speed_mbps = (downloaded / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                                    await progress_callback(downloaded, max(total_size, downloaded), speed_mbps)
                                except:
                                    pass
                    
                    # Verify download
                    if os.path.exists(download_path):
                        actual_size = os.path.getsize(download_path)
                        elapsed = asyncio.get_event_loop().time() - start_time
                        final_speed = (actual_size / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                        
                        logger.info(f"🎉 403 BYPASS SUCCESS: {filename} - Speed: {final_speed:.1f} MB/min")
                        return download_path
                    else:
                        raise Exception("File not created")
                        
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                
                # Clean up partial file
                try:
                    if os.path.exists(download_path):
                        os.remove(download_path)
                except:
                    pass
                
                if attempt == max_retries - 1:
                    logger.error("❌ All 403 bypass strategies failed")
                    return None
        
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """403-BYPASS download entry point"""
        try:
            logger.info(f"🚀 403-BYPASS download starting: {url[:50]}...")
            
            # Get file info
            file_info = await self.extract_file_info(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "File info failed"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            original_url = file_info["original_url"]
            
            if not download_url:
                raise Exception("No download URL")
            
            # 403-BYPASS download
            result = await self.download_bypass_403(download_url, filename, original_url, progress_callback)
            return result
                    
        except Exception as e:
            logger.error(f"❌ 403-BYPASS download error: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
        
