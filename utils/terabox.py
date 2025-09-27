import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote, urlparse
import aiofiles
import random
import time
from datetime import datetime

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
        self.backup_apis = [
            "https://terabox-downloader-ten.vercel.app/api",
            "https://terabox-dl.qtcloud.workers.dev/api",
            "https://teraboxdl.xcodee.workers.dev/api",
            "https://terabox.hnn.workers.dev/api"
        ]
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks
        
        # ENHANCED 403-BYPASS HEADERS
        self.bypass_strategies = [
            # Strategy 1: Chrome Desktop (Windows)
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            },
            # Strategy 2: Firefox Desktop (Windows)
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            # Strategy 3: Chrome Mobile (Android)
            {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            },
            # Strategy 4: Safari Desktop (macOS)
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            },
            # Strategy 5: Edge Desktop (Windows)
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"'
            },
            # Strategy 6: Direct approach with minimal headers
            {
                "User-Agent": "Terabox-Client/1.0",
                "Accept": "*/*",
                "Connection": "keep-alive"
            },
            # Strategy 7: Curl-like approach
            {
                "User-Agent": "curl/8.4.0",
                "Accept": "*/*"
            }
        ]

    async def get_session(self):
        """Get session with enhanced 403-bypass configuration"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                keepalive_timeout=60,
                force_close=False
            )
            
            timeout = aiohttp.ClientTimeout(
                total=1800,  # 30 minutes
                connect=45,   
                sock_read=180  
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
        return self.session

    async def extract_file_info(self, url: str, api_index: int = 0) -> dict:
        """Extract file information with backup APIs"""
        try:
            api_urls = [self.api_url] + self.backup_apis
            current_api = api_urls[api_index] if api_index < len(api_urls) else api_urls[0]
            
            logger.info(f"🔍 Extracting info: {url[:50]}... (API {api_index + 1})")
            
            api_request_url = f"{current_api}?url={quote(url)}"
            session = await self.get_session()
            
            async with session.get(api_request_url) as response:
                if response.status != 200:
                    if api_index < len(api_urls) - 1:
                        logger.warning(f"⚠️ API {api_index + 1} failed, trying backup...")
                        return await self.extract_file_info(url, api_index + 1)
                    raise Exception(f"All APIs failed: {response.status}")
                
                req = await response.json()
                
                if "✅ Status" not in req or "📜 Extracted Info" not in req:
                    if api_index < len(api_urls) - 1:
                        logger.warning(f"⚠️ Invalid response from API {api_index + 1}, trying backup...")
                        return await self.extract_file_info(url, api_index + 1)
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

    async def enhanced_403_bypass(self, download_url: str, filename: str, original_url: str, progress_callback: Optional[Callable] = None, max_attempts: int = 15) -> Optional[str]:
        """ENHANCED 403-BYPASS with more strategies and techniques"""
        download_path = os.path.join("/tmp", filename)
        
        for attempt in range(max_attempts):
            try:
                # Fresh session every few attempts
                if attempt % 3 == 0 and self.session:
                    await self.session.close()
                    self.session = None
                
                session = await self.get_session()
                
                # Choose strategy (cycle through all available)
                strategy_index = attempt % len(self.bypass_strategies)
                headers = self.bypass_strategies[strategy_index].copy()
                
                # ENHANCED BYPASS TECHNIQUES
                parsed_url = urlparse(download_url)
                domain = parsed_url.netloc
                
                # Add domain-specific enhancements
                if 'terabox' in domain.lower() or '1024tera' in domain.lower():
                    headers.update({
                        "Referer": original_url,
                        "Origin": f"https://{urlparse(original_url).netloc}",
                    })
                
                # Add random elements to avoid fingerprinting
                if attempt > 5:  # After 5 attempts, add more randomization
                    random_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    headers.update({
                        "X-Forwarded-For": random_ip,
                        "X-Real-IP": random_ip,
                        "X-Originating-IP": random_ip,
                        "CF-Connecting-IP": random_ip,
                    })
                
                # Add session/auth-like headers for higher attempts
                if attempt > 10:
                    headers.update({
                        "Authorization": f"Bearer terabox_{random.randint(100000,999999)}",
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRF-Token": f"csrf_{random.randint(100000,999999)}",
                    })
                
                logger.info(f"🚀 ENHANCED BYPASS attempt {attempt + 1}/{max_attempts}: {filename}")
                logger.info(f"🔧 Strategy: {headers.get('User-Agent', 'Unknown')[:50]}...")
                
                # Progressive delays
                if attempt > 0:
                    delay = min(2 + (attempt * 0.5), 10)  # Max 10 seconds
                    await asyncio.sleep(delay + random.uniform(0, 1))
                
                async with session.get(download_url, headers=headers) as response:
                    logger.info(f"📊 Response Status: {response.status}")
                    
                    if response.status == 403:
                        logger.error(f"❌ 403 Forbidden with strategy {attempt + 1}")
                        continue
                    elif response.status == 429:
                        logger.warning(f"⚠️ Rate limited, waiting longer...")
                        await asyncio.sleep(30)
                        continue
                    elif response.status not in [200, 206]:
                        logger.warning(f"⚠️ HTTP {response.status}, trying next strategy...")
                        continue
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    logger.info(f"🎉 SUCCESS! 403-BYPASS BREAKTHROUGH!")
                    logger.info(f"📦 Size: {get_readable_file_size(total_size)}")
                    
                    downloaded = 0
                    start_time = time.time()
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback every 16MB
                            if progress_callback and downloaded % (16 * 1024 * 1024) < self.chunk_size:
                                try:
                                    elapsed = time.time() - start_time
                                    speed_mbps = (downloaded / (1024 * 1024)) / max(elapsed / 60, 0.01)
                                    await progress_callback(downloaded, max(total_size, downloaded), speed_mbps)
                                except:
                                    pass
                    
                    # Verify download
                    if os.path.exists(download_path):
                        actual_size = os.path.getsize(download_path)
                        elapsed = time.time() - start_time
                        final_speed = (actual_size / (1024 * 1024)) / max(elapsed / 60, 0.01)
                        
                        logger.info(f"🎉 403-BYPASS SUCCESS: {filename} - Speed: {final_speed:.1f} MB/min")
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
        
        logger.error("❌ All enhanced 403-bypass strategies exhausted")
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Enhanced download with improved 403-bypass"""
        try:
            logger.info(f"🚀 ENHANCED 403-BYPASS download starting: {url[:50]}...")
            
            # Get file info
            file_info = await self.extract_file_info(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "File info failed"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            original_url = file_info["original_url"]
            
            if not download_url:
                raise Exception("No download URL")
            
            # Enhanced 403-bypass download with more strategies
            result = await self.enhanced_403_bypass(download_url, filename, original_url, progress_callback)
            return result
                    
        except Exception as e:
            logger.error(f"❌ Enhanced download error: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
        
