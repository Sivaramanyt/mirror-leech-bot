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
import json
import hashlib

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

class NuclearTeraboxDownloader:
    def __init__(self):
        self.session = None
        
        # MULTIPLE API ENDPOINTS
        self.api_endpoints = [
            "https://wdzone-terabox-api.vercel.app/api",
            "https://terabox-downloader-ten.vercel.app/api",
            "https://terabox-dl.qtcloud.workers.dev/api",
            "https://teraboxdl.xcodee.workers.dev/api",
            "https://terabox.hnn.workers.dev/api",
            "https://terabox-api-delta.vercel.app/api",
            "https://api-terabox.onrender.com/api",
            "https://teraboxapi.nephobox.com/api"
        ]
        
        # FREE PROXY LISTS (Basic ones - can be enhanced)
        self.proxy_list = [
            None,  # No proxy first
            # Add working proxies here if needed
            # "http://proxy1:port",
            # "http://proxy2:port",
        ]
        
        self.chunk_size = 4 * 1024 * 1024  # 4MB chunks for stability
        
        # NUCLEAR 403-BYPASS STRATEGIES
        self.nuclear_strategies = [
            # Strategy 1: Standard Chrome
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "DNT": "1",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "cross-site"
            },
            # Strategy 2: Mobile Chrome
            {
                "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            },
            # Strategy 3: Firefox
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            },
            # Strategy 4: Safari
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            },
            # Strategy 5: Edge
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive"
            },
            # Strategy 6: Opera
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
                "Accept": "*/*",
                "Connection": "keep-alive"
            },
            # Strategy 7: Old Chrome
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "Accept": "*/*",
                "Connection": "keep-alive"
            },
            # Strategy 8: Minimal headers
            {
                "User-Agent": "TeraboxDownloader/1.0",
                "Accept": "*/*"
            },
            # Strategy 9: cURL simulation
            {
                "User-Agent": "curl/8.4.0",
                "Accept": "*/*"
            },
            # Strategy 10: Wget simulation
            {
                "User-Agent": "Wget/1.21.3",
                "Accept": "*/*"
            }
        ]

    async def get_fresh_session(self, proxy=None):
        """Get completely fresh session"""
        if self.session:
            try:
                await self.session.close()
            except:
                pass
        
        connector_kwargs = {
            'limit': 30,
            'limit_per_host': 10,
            'ttl_dns_cache': 300,
            'use_dns_cache': True,
            'enable_cleanup_closed': True,
            'keepalive_timeout': 60,
            'force_close': False,
            'family': 0  # Allow both IPv4 and IPv6
        }
        
        if proxy:
            connector_kwargs['proxy'] = proxy
        
        connector = aiohttp.TCPConnector(**connector_kwargs)
        
        timeout = aiohttp.ClientTimeout(
            total=1800,  # 30 minutes
            connect=60,   
            sock_read=300  
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self.session

    async def try_all_apis(self, url: str) -> dict:
        """Try all API endpoints until one works"""
        for i, api_url in enumerate(self.api_endpoints):
            try:
                logger.info(f"🔍 Trying API {i+1}/{len(self.api_endpoints)}: {api_url.split('//')[1].split('/')[0]}")
                
                session = await self.get_fresh_session()
                api_request_url = f"{api_url}?url={quote(url)}"
                
                async with session.get(api_request_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        req = await response.json()
                        
                        # Check response format
                        if "✅ Status" in req and "📜 Extracted Info" in req:
                            extracted_info = req["📜 Extracted Info"]
                            if extracted_info and len(extracted_info) > 0:
                                data = extracted_info[0]
                                filename = data.get("📂 Title", "terabox_file")
                                download_url = data.get("🔽 Direct Download Link", "")
                                
                                if download_url:
                                    if not os.path.splitext(filename)[1]:
                                        filename += ".mp4"
                                    
                                    logger.info(f"✅ API {i+1} SUCCESS: {filename}")
                                    logger.info(f"🔗 Download URL: {download_url[:80]}...")
                                    
                                    return {
                                        "success": True,
                                        "filename": sanitize_filename(filename),
                                        "download_url": download_url,
                                        "title": filename,
                                        "original_url": url
                                    }
                        
                        logger.warning(f"⚠️ API {i+1} invalid response format")
                    else:
                        logger.warning(f"⚠️ API {i+1} HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ API {i+1} timeout")
            except Exception as e:
                logger.warning(f"⚠️ API {i+1} error: {str(e)[:100]}")
        
        return {"success": False, "error": "All APIs failed"}

    async def nuclear_403_bypass(self, download_url: str, filename: str, original_url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """NUCLEAR 403-BYPASS with extreme measures"""
        download_path = os.path.join("/tmp", filename)
        
        # NUCLEAR APPROACH: Try every combination
        max_attempts = 50  # Increased attempts
        
        for attempt in range(max_attempts):
            try:
                # Strategy selection with cycling
                strategy_index = attempt % len(self.nuclear_strategies)
                proxy_index = (attempt // len(self.nuclear_strategies)) % len(self.proxy_list)
                
                headers = self.nuclear_strategies[strategy_index].copy()
                proxy = self.proxy_list[proxy_index]
                
                # Get fresh session every 3 attempts or when switching proxies
                if attempt % 3 == 0 or proxy:
                    session = await self.get_fresh_session(proxy)
                else:
                    session = self.session or await self.get_fresh_session()
                
                # ADVANCED SPOOFING TECHNIQUES
                parsed_original = urlparse(original_url)
                parsed_download = urlparse(download_url)
                
                # Add referrer and origin
                headers.update({
                    "Referer": original_url,
                    "Origin": f"https://{parsed_original.netloc}",
                })
                
                # Advanced spoofing for higher attempts
                if attempt >= 10:
                    # Fake IP headers
                    fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    headers.update({
                        "X-Forwarded-For": fake_ip,
                        "X-Real-IP": fake_ip,
                        "X-Originating-IP": fake_ip,
                        "CF-Connecting-IP": fake_ip,
                        "Client-IP": fake_ip,
                    })
                
                if attempt >= 20:
                    # Add session/auth simulation
                    session_id = hashlib.md5(f"{attempt}{time.time()}".encode()).hexdigest()[:16]
                    headers.update({
                        "Authorization": f"Bearer {session_id}",
                        "X-Session-ID": session_id,
                        "X-Request-ID": str(random.randint(100000, 999999)),
                        "X-Terabox-Client": "web",
                    })
                
                if attempt >= 30:
                    # Browser cache simulation
                    headers.update({
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                        "If-None-Match": f'"{random.randint(100000, 999999)}"',
                    })
                
                proxy_text = f" via {proxy}" if proxy else ""
                logger.info(f"🚀 NUCLEAR BYPASS attempt {attempt + 1}/{max_attempts}: {filename}")
                logger.info(f"🔧 Strategy {strategy_index + 1}: {headers.get('User-Agent', 'Unknown')[:50]}...{proxy_text}")
                
                # Progressive delays with randomization
                if attempt > 0:
                    base_delay = min(1 + (attempt * 0.3), 8)  # Max 8 seconds
                    actual_delay = base_delay + random.uniform(0, 2)
                    await asyncio.sleep(actual_delay)
                
                # Add random delay to avoid pattern detection
                if attempt >= 5:
                    await asyncio.sleep(random.uniform(0.1, 1.0))
                
                # THE NUCLEAR REQUEST
                async with session.get(download_url, headers=headers) as response:
                    status = response.status
                    content_length = response.headers.get('content-length', '0')
                    
                    logger.info(f"📊 Response: HTTP {status}, Content-Length: {content_length}")
                    
                    if status == 403:
                        logger.error(f"❌ 403 with strategy {strategy_index + 1}{proxy_text}")
                        continue
                    elif status == 429:
                        logger.warning(f"⚠️ Rate limited, waiting 30s...")
                        await asyncio.sleep(30 + random.uniform(0, 10))
                        continue
                    elif status not in [200, 206]:
                        logger.warning(f"⚠️ HTTP {status}, trying next...")
                        continue
                    
                    total_size = int(content_length) if content_length.isdigit() else 0
                    
                    logger.info(f"🎉 NUCLEAR BREAKTHROUGH! 🎉")
                    logger.info(f"🚀 Strategy {strategy_index + 1} SUCCEEDED!")
                    logger.info(f"📦 Size: {get_readable_file_size(total_size)}")
                    
                    # Download with progress
                    downloaded = 0
                    start_time = time.time()
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback every 8MB
                            if progress_callback and downloaded % (8 * 1024 * 1024) < self.chunk_size:
                                try:
                                    elapsed = time.time() - start_time
                                    speed_mbps = (downloaded / (1024 * 1024)) / max(elapsed / 60, 0.01)
                                    await progress_callback(downloaded, max(total_size, downloaded), speed_mbps)
                                except:
                                    pass
                    
                    # Verify download
                    if os.path.exists(download_path) and os.path.getsize(download_path) > 0:
                        actual_size = os.path.getsize(download_path)
                        elapsed = time.time() - start_time
                        final_speed = (actual_size / (1024 * 1024)) / max(elapsed / 60, 0.01)
                        
                        logger.info(f"🎉 NUCLEAR SUCCESS: {filename}")
                        logger.info(f"🚀 Speed: {final_speed:.1f} MB/min")
                        logger.info(f"💣 Breakthrough on attempt {attempt + 1}")
                        return download_path
                    else:
                        logger.warning("⚠️ File not created properly")
                        
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Attempt {attempt + 1} timeout")
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} error: {str(e)[:100]}")
                
                # Clean up partial file
                try:
                    if os.path.exists(download_path):
                        os.remove(download_path)
                except:
                    pass
        
        logger.error("💥 NUCLEAR BYPASS EXHAUSTED - Terabox defenses too strong!")
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Nuclear download with all APIs and bypass strategies"""
        try:
            logger.info(f"💣 NUCLEAR 403-BYPASS INITIATED: {url[:50]}...")
            
            # Try all API endpoints
            file_info = await self.try_all_apis(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "All APIs failed"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            original_url = file_info["original_url"]
            
            if not download_url:
                raise Exception("No download URL from any API")
            
            # Nuclear 403-bypass
            result = await self.nuclear_403_bypass(download_url, filename, original_url, progress_callback)
            return result
                    
        except Exception as e:
            logger.error(f"💥 Nuclear download error: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = NuclearTeraboxDownloader()
    
