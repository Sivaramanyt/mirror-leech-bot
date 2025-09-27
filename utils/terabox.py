import os
import re
import json
import asyncio
import aiohttp
import aiofiles
import logging
from typing import Optional, Callable
from urllib.parse import parse_qs, urlparse, unquote
import base64

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

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks
        
        # Headers with proper compression support
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Remove brotli to fix compression error
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    async def get_session(self):
        """Get or create aiohttp session with proper configuration"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=20,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=300, connect=30, sock_read=60)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
        return self.session

    async def extract_surl_from_url(self, url: str) -> Optional[str]:
        """Extract surl from various Terabox URL formats with better cleaning"""
        try:
            logger.info(f"🔍 Extracting surl from: {url}")
            
            # Clean up URL first
            url = url.strip()
            
            # Handle different URL formats with more patterns
            patterns = [
                r'surl=([A-Za-z0-9_-]+)',
                r'/s/([A-Za-z0-9_-]+)',
                r'[?&]surl=([A-Za-z0-9_-]+)',
                r'terasharelink\.com/s/([A-Za-z0-9_-]+)',
                r'terabox\.com/s/([A-Za-z0-9_-]+)',
                r'nephobox\.com/s/([A-Za-z0-9_-]+)',
                r'4funbox\.com/s/([A-Za-z0-9_-]+)',
                r'mirrobox\.com/s/([A-Za-z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    surl = match.group(1)
                    # Clean up any trailing characters
                    surl = re.sub(r'[^A-Za-z0-9_-].*$', '', surl)
                    logger.info(f"✅ Extracted surl: {surl}")
                    return surl
            
            # Manual parsing as last resort
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

    async def try_working_apis(self, surl: str) -> dict:
        """Try working API endpoints with proper error handling"""
        # Updated working APIs
        api_endpoints = [
            f"https://wdzone-terabox-api.vercel.app/api?url=https://terabox.com/s/{surl}",
            f"https://terabox-api-delta.vercel.app/api?url=https://terabox.com/s/{surl}",
            f"https://terabox-downloader-api.vercel.app/api?url=https://terabox.com/s/{surl}",
            f"https://api-terabox.onrender.com/api?url=https://terabox.com/s/{surl}",
            # Backup with different URL formats
            f"https://wdzone-terabox-api.vercel.app/api?url=https://terasharelink.com/s/{surl}",
            f"https://wdzone-terabox-api.vercel.app/api?url=https://nephobox.com/s/{surl}"
        ]
        
        session = await self.get_session()
        
        for i, api_url in enumerate(api_endpoints):
            try:
                domain = api_url.split('//')[1].split('/')[0]
                logger.info(f"🔄 API {i+1}/{len(api_endpoints)}: {domain}")
                
                # Disable compression to avoid brotli errors
                headers = {'Accept-Encoding': 'identity'}
                
                async with session.get(api_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    logger.info(f"📊 API {i+1} Response: HTTP {response.status}")
                    
                    if response.status == 200:
                        try:
                            text_content = await response.text()
                            result = json.loads(text_content)
                            
                            # Check for successful response
                            if "✅ Status" in result and "📜 Extracted Info" in result:
                                extracted_info = result["📜 Extracted Info"]
                                if extracted_info and len(extracted_info) > 0:
                                    data = extracted_info[0]
                                    filename = data.get("📂 Title", "terabox_file")
                                    download_url = data.get("🔽 Direct Download Link", "")
                                    
                                    if download_url and filename:
                                        # Clean filename
                                        if not os.path.splitext(filename)[1]:
                                            # Guess extension from URL or default to .mp4
                                            if any(ext in download_url.lower() for ext in ['.mp4', '.mkv', '.avi']):
                                                filename += '.mp4'
                                            elif any(ext in download_url.lower() for ext in ['.mp3', '.wav', '.flac']):
                                                filename += '.mp3'
                                            else:
                                                filename += '.mp4'  # Default for video
                                        
                                        logger.info(f"✅ API {i+1} SUCCESS: {filename}")
                                        logger.info(f"🔗 Download URL: {download_url[:60]}...")
                                        
                                        return {
                                            "success": True,
                                            "filename": sanitize_filename(filename),
                                            "download_url": download_url,
                                            "api_source": domain
                                        }
                            
                            logger.warning(f"⚠️ API {i+1}: Invalid response format")
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"⚠️ API {i+1}: JSON decode error - {e}")
                        except Exception as e:
                            logger.warning(f"⚠️ API {i+1}: Response processing error - {e}")
                    
                    elif response.status == 500:
                        logger.warning(f"⚠️ API {i+1}: Server error (500)")
                    elif response.status == 403:
                        logger.warning(f"⚠️ API {i+1}: Forbidden (403)")
                    else:
                        logger.warning(f"⚠️ API {i+1}: HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ API {i+1}: Timeout")
            except aiohttp.ClientError as e:
                logger.warning(f"⚠️ API {i+1}: Connection error - {str(e)[:100]}")
            except Exception as e:
                logger.warning(f"⚠️ API {i+1}: Unexpected error - {str(e)[:100]}")
        
        logger.error("❌ All API endpoints failed")
        return {"success": False, "error": "All API endpoints failed"}

    async def download_file_safe(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Safe download with multiple retry strategies"""
        download_path = os.path.join("/tmp", filename)
        
        # Multiple download strategies
        strategies = [
            {'headers': self.headers.copy(), 'method': 'standard'},
            {'headers': {'User-Agent': 'curl/7.68.0', 'Accept': '*/*'}, 'method': 'curl'},
            {'headers': {'User-Agent': 'wget/1.20.3', 'Accept': '*/*'}, 'method': 'wget'},
            {'headers': {}, 'method': 'minimal'}
        ]
        
        for attempt, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"🚀 Download attempt {attempt}/4 ({strategy['method']}): {filename}")
                
                session = await self.get_session()
                headers = strategy['headers']
                
                async with session.get(download_url, headers=headers) as response:
                    logger.info(f"📊 Download Response: HTTP {response.status}")
                    
                    if response.status not in [200, 206]:
                        logger.warning(f"⚠️ Attempt {attempt}: HTTP {response.status}")
                        if attempt < len(strategies):
                            await asyncio.sleep(2)  # Wait before retry
                            continue
                        else:
                            return None
                    
                    total_size = int(response.headers.get('content-length', 0))
                    logger.info(f"📦 File size: {get_readable_file_size(total_size)}")
                    
                    downloaded = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                                
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback every 16MB
                            if progress_callback and downloaded % (16 * 1024 * 1024) < self.chunk_size:
                                elapsed = asyncio.get_event_loop().time() - start_time
                                speed_mbps = (downloaded / (1024 * 1024)) / max(elapsed / 60, 0.01)
                                
                                try:
                                    await progress_callback(downloaded, max(total_size, downloaded), speed_mbps)
                                except Exception as e:
                                    logger.warning(f"Progress callback error: {e}")
                    
                    # Verify download
                    if os.path.exists(download_path):
                        final_size = os.path.getsize(download_path)
                        if final_size > 0:
                            elapsed = asyncio.get_event_loop().time() - start_time
                            final_speed = (final_size / (1024 * 1024)) / max(elapsed / 60, 0.01)
                            
                            logger.info(f"✅ Download complete: {get_readable_file_size(final_size)} at {final_speed:.1f} MB/min")
                            return download_path
                        else:
                            logger.warning(f"⚠️ Attempt {attempt}: File is empty")
                    else:
                        logger.warning(f"⚠️ Attempt {attempt}: File not created")
                    
                    if attempt < len(strategies):
                        await asyncio.sleep(3)  # Wait before retry
                        
            except Exception as e:
                logger.error(f"❌ Attempt {attempt} error: {str(e)[:100]}")
                if attempt < len(strategies):
                    await asyncio.sleep(5)  # Wait before retry
                
                # Clean up partial file
                try:
                    if os.path.exists(download_path):
                        os.remove(download_path)
                except:
                    pass
        
        logger.error("❌ All download attempts failed")
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Main download method - comprehensive approach"""
        try:
            logger.info(f"🎯 COMPREHENSIVE TERABOX DOWNLOAD: {url[:50]}...")
            
            # Step 1: Extract surl
            surl = await self.extract_surl_from_url(url)
            if not surl:
                logger.error("❌ Could not extract surl from URL")
                return None
            
            logger.info(f"🔑 Using surl: {surl}")
            
            # Step 2: Try working APIs
            file_info = await self.try_working_apis(surl)
            if not file_info.get("success"):
                logger.error(f"❌ API extraction failed: {file_info.get('error')}")
                return None
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            api_source = file_info.get("api_source", "unknown")
            
            logger.info(f"📄 File: {filename}")
            logger.info(f"🌐 Source API: {api_source}")
            
            # Step 3: Download with retry strategies
            return await self.download_file_safe(download_url, filename, progress_callback)
            
        except Exception as e:
            logger.error(f"❌ Comprehensive download error: {e}")
            return None

    # Compatibility methods
    async def extract_file_info(self, url: str, api_index: int = 0) -> dict:
        """Compatibility method"""
        surl = await self.extract_surl_from_url(url)
        if not surl:
            return {"success": False, "error": "Could not extract surl"}
        
        return await self.try_working_apis(surl)

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
                    
