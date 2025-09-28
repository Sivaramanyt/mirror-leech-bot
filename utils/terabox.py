import os
import re
import json
import asyncio
import aiohttp
import aiofiles
import logging
import time
import hashlib
from typing import Optional, Callable
from urllib.parse import parse_qs, urlparse, unquote

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = re.sub(r'[^\w\s.-]', '_', filename)
    return filename[:200].strip()

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

class OptimizedTeraboxDownloader:
    def __init__(self):
        self.session = None
        self.chunk_size = 16 * 1024 * 1024  # 16MB chunks for faster download
        
        # Optimized headers for maximum speed
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # No brotli
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache'
        }

    async def get_session(self):
        """Get optimized session for maximum speed"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=50,           # Increased connection pool
                limit_per_host=20,  # More concurrent connections
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=120,  # Longer keepalive
                enable_cleanup_closed=True,
                family=0  # Allow both IPv4 and IPv6
            )
            
            timeout = aiohttp.ClientTimeout(
                total=3600,      # 1 hour total timeout
                connect=30,      # Quick connect timeout
                sock_read=300    # 5 minutes read timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
        return self.session

    async def extract_surl_from_url(self, url: str) -> Optional[str]:
        """Extract surl from various Terabox URL formats"""
        try:
            logger.info(f"🔍 Extracting surl from: {url}")
            url = url.strip()
            
            # ✅ FIXED: Added teraboxlink.com pattern
            patterns = [
                r'surl=([A-Za-z0-9_-]+)',
                r'/s/([A-Za-z0-9_-]+)',
                r'[?&]surl=([A-Za-z0-9_-]+)',
                r'terasharelink\.com/s/([A-Za-z0-9_-]+)',
                r'teraboxlink\.com/s/([A-Za-z0-9_-]+)',    # ← ADDED THIS LINE!
                r'terabox\.com/s/([A-Za-z0-9_-]+)',
                r'nephobox\.com/s/([A-Za-z0-9_-]+)',
                r'4funbox\.com/s/([A-Za-z0-9_-]+)',
                r'mirrobox\.com/s/([A-Za-z0-9_-]+)',
                r'momerybox\.com/s/([A-Za-z0-9_-]+)',
                r'tibibox\.com/s/([A-Za-z0-9_-]+)',
                r'1024tera\.com/s/([A-Za-z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    surl = match.group(1)
                    surl = re.sub(r'[^A-Za-z0-9_-].*$', '', surl)
                    logger.info(f"✅ Extracted surl: {surl}")
                    return surl
            
            parsed_url = urlparse(url)
            if '/s/' in parsed_url.path:
                path_parts = parsed_url.path.split('/s/')
                if len(path_parts) > 1:
                    surl = path_parts[-1].split('/')[0].split('?')[0].split('#')[0]
                    surl = re.sub(r'[^A-Za-z0-9_-].*$', '', surl)
                    if surl:
                        logger.info(f"✅ Manually extracted surl: {surl}")
                        return surl
            
            logger.error(f"❌ Could not extract surl from: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting surl: {e}")
            return None

    async def get_fastest_download_url(self, surl: str) -> dict:
        """Try APIs in order of speed and reliability"""
        # Prioritized API endpoints (fastest first)
        priority_apis = [
            f"https://wdzone-terabox-api.vercel.app/api?url=https://terabox.com/s/{surl}",
            f"https://terabox-api-delta.vercel.app/api?url=https://terabox.com/s/{surl}",
            f"https://teraboxapi.nephobox.com/api?url=https://terabox.com/s/{surl}",
            # ✅ FIXED: Added teraboxlink.com API calls
            f"https://wdzone-terabox-api.vercel.app/api?url=https://teraboxlink.com/s/{surl}",
            f"https://wdzone-terabox-api.vercel.app/api?url=https://terasharelink.com/s/{surl}",
            f"https://wdzone-terabox-api.vercel.app/api?url=https://nephobox.com/s/{surl}"
        ]
        
        session = await self.get_session()
        
        for i, api_url in enumerate(priority_apis):
            try:
                domain = api_url.split('//')[1].split('/')[0]
                logger.info(f"🚀 FAST-API {i+1}/{len(priority_apis)}: {domain}")
                
                headers = {'Accept-Encoding': 'identity'}
                
                async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    logger.info(f"⚡ API {i+1} Response: HTTP {response.status}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            
                            if "✅ Status" in result and "📜 Extracted Info" in result:
                                extracted_info = result["📜 Extracted Info"]
                                if extracted_info and len(extracted_info) > 0:
                                    data = extracted_info[0]
                                    filename = data.get("📂 Title", "terabox_file")
                                    download_url = data.get("🔽 Direct Download Link", "")
                                    
                                    if download_url and filename:
                                        if not os.path.splitext(filename)[1]:
                                            filename += '.mp4'
                                        
                                        logger.info(f"⚡ FAST-SUCCESS {i+1}: {filename}")
                                        
                                        return {
                                            "success": True,
                                            "filename": sanitize_filename(filename),
                                            "download_url": download_url,
                                            "api_source": domain,
                                            "priority": i + 1
                                        }
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ API {i+1}: JSON decode error")
                    
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ API {i+1}: Timeout (trying next)")
                continue
            except Exception as e:
                logger.warning(f"⚠️ API {i+1}: Error - {str(e)[:50]}")
                continue
        
        logger.error("❌ All fast APIs failed")
        return {"success": False, "error": "All APIs failed"}

    async def smart_resume_download(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Smart download with REAL resume capability"""
        download_path = os.path.join("/tmp", filename)
        temp_path = f"{download_path}.tmp"
        
        try:
            session = await self.get_session()
            
            # Check existing partial download
            resume_pos = 0
            if os.path.exists(temp_path):
                resume_pos = os.path.getsize(temp_path)
                logger.info(f"📂 SMART RESUME from {get_readable_file_size(resume_pos)}")
            elif os.path.exists(download_path):
                # File exists but might be incomplete
                file_size = os.path.getsize(download_path)
                logger.info(f"📂 File exists: {get_readable_file_size(file_size)}")
                return download_path
            
            # Fast download strategies (ordered by success rate)
            strategies = [
                {
                    'name': 'HIGH_SPEED',
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                        'Accept': '*/*',
                        'Connection': 'keep-alive',
                        'Accept-Encoding': 'identity'
                    }
                },
                {
                    'name': 'DIRECT_STREAM', 
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                        'Accept': '*/*'
                    }
                },
                {
                    'name': 'MOBILE_AGENT',
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
                        'Accept': '*/*'
                    }
                }
            ]
            
            for attempt, strategy in enumerate(strategies, 1):
                try:
                    logger.info(f"🚀 SMART DOWNLOAD attempt {attempt}/3 ({strategy['name']}): {filename}")
                    
                    headers = strategy['headers'].copy()
                    
                    # Add range header for resume
                    if resume_pos > 0:
                        headers['Range'] = f'bytes={resume_pos}-'
                        logger.info(f"📍 Resume from byte: {resume_pos}")
                    
                    async with session.get(download_url, headers=headers) as response:
                        status = response.status
                        logger.info(f"📊 Response: HTTP {status}")
                        
                        if status not in [200, 206]:
                            logger.warning(f"⚠️ Attempt {attempt}: HTTP {status}")
                            if attempt < len(strategies):
                                await asyncio.sleep(2)  # Brief pause before retry
                                continue
                            else:
                                return None
                        
                        # Get file size info
                        content_length = response.headers.get('content-length', '0')
                        total_size = int(content_length) if content_length.isdigit() else 0
                        
                        if resume_pos > 0 and status == 206:
                            # Partial content - add resume position
                            total_size += resume_pos
                            logger.info(f"📦 Total size: {get_readable_file_size(total_size)} (resuming)")
                        else:
                            logger.info(f"📦 Total size: {get_readable_file_size(total_size)} (fresh)")
                        
                        # Start download with progress tracking
                        downloaded = resume_pos
                        start_time = time.time()
                        last_progress_time = start_time
                        
                        # Open file in append mode if resuming, write mode if fresh
                        mode = 'ab' if resume_pos > 0 and status == 206 else 'wb'
                        
                        async with aiofiles.open(temp_path, mode) as f:
                            async for chunk in response.content.iter_chunked(self.chunk_size):
                                if not chunk:
                                    break
                                    
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Progress callback every 2 seconds or 32MB
                                current_time = time.time()
                                if (progress_callback and 
                                    (current_time - last_progress_time >= 2.0 or 
                                     downloaded % (32 * 1024 * 1024) < self.chunk_size)):
                                    
                                    elapsed = current_time - start_time
                                    speed_mbps = (downloaded / (1024 * 1024)) / max(elapsed / 60, 0.01)
                                    
                                    try:
                                        await progress_callback(downloaded, max(total_size, downloaded), speed_mbps)
                                        last_progress_time = current_time
                                    except Exception as e:
                                        logger.warning(f"Progress callback error: {e}")
                        
                        # Verify and finalize download
                        if os.path.exists(temp_path):
                            final_size = os.path.getsize(temp_path)
                            if final_size > 0:
                                # Move temp file to final location
                                os.rename(temp_path, download_path)
                                
                                elapsed = time.time() - start_time
                                final_speed = (final_size / (1024 * 1024)) / max(elapsed / 60, 0.01)
                                
                                logger.info(f"✅ SMART SUCCESS: {get_readable_file_size(final_size)} at {final_speed:.1f} MB/min")
                                return download_path
                            else:
                                logger.warning(f"⚠️ Attempt {attempt}: Downloaded file is empty")
                        else:
                            logger.warning(f"⚠️ Attempt {attempt}: Temp file not created")
                        
                        if attempt < len(strategies):
                            await asyncio.sleep(3)  # Wait before retry
                            
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Attempt {attempt}: Download timeout")
                    if attempt < len(strategies):
                        await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"❌ Attempt {attempt} error: {str(e)[:100]}")
                    if attempt < len(strategies):
                        await asyncio.sleep(5)
                
                # Clean up failed temp file
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except:
                    pass
            
            logger.error("❌ All smart download attempts failed")
            return None
            
        except Exception as e:
            logger.error(f"❌ Smart download error: {e}")
            return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Optimized download with smart resume"""
        try:
            logger.info(f"⚡ OPTIMIZED TERABOX DOWNLOAD: {url[:50]}...")
            
            # Step 1: Fast surl extraction
            surl = await self.extract_surl_from_url(url)
            if not surl:
                logger.error("❌ Could not extract surl")
                return None
            
            logger.info(f"🔑 Using surl: {surl}")
            
            # Step 2: Get fastest API response
            file_info = await self.get_fastest_download_url(surl)
            if not file_info.get("success"):
                logger.error(f"❌ Fast API failed: {file_info.get('error')}")
                return None
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            api_source = file_info.get("api_source", "unknown")
            priority = file_info.get("priority", 0)
            
            logger.info(f"📄 File: {filename}")
            logger.info(f"🚀 Source: {api_source} (Priority {priority})")
            
            # Step 3: Smart resume download
            return await self.smart_resume_download(download_url, filename, progress_callback)
            
        except Exception as e:
            logger.error(f"❌ Optimized download error: {e}")
            return None

    # Compatibility methods
    async def extract_file_info(self, url: str, api_index: int = 0) -> dict:
        """Compatibility method"""
        surl = await self.extract_surl_from_url(url)
        if not surl:
            return {"success": False, "error": "Could not extract surl"}
        
        return await self.get_fastest_download_url(surl)

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = OptimizedTeraboxDownloader()
        
