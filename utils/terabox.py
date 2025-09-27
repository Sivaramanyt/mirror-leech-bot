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
        self.chunk_size = 10 * 1024 * 1024  # 10MB chunks
        
        # Headers that mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=30,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60
            )
            
            timeout = aiohttp.ClientTimeout(total=1800, connect=60, sock_read=600)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
        return self.session

    async def extract_surl_from_url(self, url: str) -> Optional[str]:
        """Extract surl from various Terabox URL formats"""
        try:
            # Handle different URL formats
            patterns = [
                r'surl=([A-Za-z0-9_-]+)',
                r'/s/([A-Za-z0-9_-]+)',
                r'[?&]surl=([A-Za-z0-9_-]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # If direct surl extraction fails, try parsing URL
            parsed_url = urlparse(url)
            if '/s/' in parsed_url.path:
                surl = parsed_url.path.split('/s/')[-1].split('/')[0]
                if surl:
                    return surl
            
            # Check query parameters
            query_params = parse_qs(parsed_url.query)
            if 'surl' in query_params:
                return query_params['surl'][0]
                
            logger.warning(f"Could not extract surl from URL: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting surl: {e}")
            return None

    async def extract_data_from_html(self, html_content: str) -> Optional[dict]:
        """Extract data from HTML with multiple methods"""
        try:
            # Method 1: Look for window.yunData or similar
            data_patterns = [
                r'window\.yunData\s*=\s*({.+?});',
                r'yunData\s*=\s*({.+?});',
                r'window\.globalData\s*=\s*({.+?});',
                r'globalData\s*=\s*({.+?});',
                r'window\.pageInfo\s*=\s*({.+?});',
                r'pageInfo\s*=\s*({.+?});'
            ]
            
            for pattern in data_patterns:
                matches = re.finditer(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match.group(1))
                        if self.validate_extracted_data(data):
                            logger.info("✅ Successfully extracted data (Method 1)")
                            return data
                    except json.JSONDecodeError:
                        continue
            
            # Method 2: Look for specific file data patterns
            file_patterns = [
                r'"server_filename":\s*"([^"]+)"[^}]*"fs_id":\s*(\d+)[^}]*"size":\s*(\d+)',
                r'"filename":\s*"([^"]+)"[^}]*"fs_id":\s*(\d+)[^}]*"size":\s*(\d+)',
            ]
            
            for pattern in file_patterns:
                match = re.search(pattern, html_content)
                if match:
                    filename = match.group(1)
                    fs_id = match.group(2)
                    size = int(match.group(3))
                    
                    logger.info("✅ Successfully extracted data (Method 2)")
                    return {
                        'file_list': [{
                            'server_filename': filename,
                            'fs_id': fs_id,
                            'size': size
                        }]
                    }
            
            # Method 3: Look for any JSON-like structures with file info
            json_blocks = re.finditer(r'({[^{}]*(?:{[^{}]*}[^{}]*)*})', html_content)
            for match in json_blocks:
                try:
                    data = json.loads(match.group(1))
                    if self.validate_extracted_data(data):
                        logger.info("✅ Successfully extracted data (Method 3)")
                        return data
                except json.JSONDecodeError:
                    continue
            
            logger.warning("Could not extract data using any method")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting data from HTML: {e}")
            return None

    def validate_extracted_data(self, data: dict) -> bool:
        """Validate if extracted data contains file information"""
        try:
            # Check for file_list or similar structures
            if 'file_list' in data and isinstance(data['file_list'], list):
                return len(data['file_list']) > 0
            
            if 'list' in data and isinstance(data['list'], list):
                return len(data['list']) > 0
            
            # Check for direct file info
            required_keys = ['server_filename', 'fs_id', 'size']
            if any(key in data for key in required_keys):
                return True
            
            return False
        except:
            return False

    async def get_file_info(self, surl: str) -> dict:
        """Get file information using surl - Enhanced method"""
        try:
            session = await self.get_session()
            
            # Step 1: Get the sharing page
            share_url = f"https://www.terabox.com/s/{surl}"
            
            logger.info(f"🔍 Accessing share page: {share_url}")
            
            async with session.get(share_url) as response:
                if response.status != 200:
                    logger.error(f"Share page returned {response.status}")
                    return {"success": False, "error": f"Share page error: {response.status}"}
                
                html_content = await response.text()
                
            # Step 2: Extract data from HTML
            extracted_data = await self.extract_data_from_html(html_content)
            
            if not extracted_data:
                logger.info("🔄 HTML extraction failed, trying fallback APIs...")
                return await self.get_file_info_fallback(surl)
            
            # Step 3: Process extracted data
            file_list = []
            
            # Check various possible locations for file list
            for key in ['file_list', 'list', 'items', 'data']:
                if key in extracted_data:
                    if isinstance(extracted_data[key], list):
                        file_list = extracted_data[key]
                        break
                    elif isinstance(extracted_data[key], dict) and 'list' in extracted_data[key]:
                        file_list = extracted_data[key]['list']
                        break
            
            # If no file list found, check if data itself is file info
            if not file_list and self.validate_extracted_data(extracted_data):
                file_list = [extracted_data]
            
            if not file_list:
                logger.error("No files found in extracted data")
                return await self.get_file_info_fallback(surl)
            
            # Process first file
            file_item = file_list[0]
            
            filename = file_item.get('server_filename', file_item.get('filename', 'terabox_file'))
            file_size = int(file_item.get('size', 0))
            fs_id = str(file_item.get('fs_id', ''))
            
            logger.info(f"✅ File found: {filename} ({get_readable_file_size(file_size)})")
            
            # Step 4: Get download link
            download_url = await self.get_download_link(surl, fs_id, extracted_data)
            
            if not download_url:
                logger.info("🔄 Direct method failed, trying fallback APIs...")
                return await self.get_file_info_fallback(surl)
            
            return {
                "success": True,
                "filename": sanitize_filename(filename),
                "download_url": download_url,
                "file_size": file_size,
                "fs_id": fs_id
            }
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return await self.get_file_info_fallback(surl)

    async def get_file_info_fallback(self, surl: str) -> dict:
        """Fallback method using working APIs"""
        try:
            api_endpoints = [
                f"https://wdzone-terabox-api.vercel.app/api?url=https://terabox.com/s/{surl}",
                f"https://terabox-downloader-ten.vercel.app/api?url=https://terabox.com/s/{surl}",
                f"https://terabox-dl.qtcloud.workers.dev/api?url=https://terabox.com/s/{surl}",
                f"https://teraboxdl.xcodee.workers.dev/api?url=https://terabox.com/s/{surl}"
            ]
            
            session = await self.get_session()
            
            for api_url in api_endpoints:
                try:
                    logger.info(f"🔄 Trying fallback API: {api_url.split('//')[1].split('/')[0]}")
                    
                    async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            if "📜 Extracted Info" in result:
                                extracted_info = result["📜 Extracted Info"]
                                if extracted_info and len(extracted_info) > 0:
                                    data = extracted_info[0]
                                    filename = data.get("📂 Title", "terabox_file")
                                    download_url = data.get("🔽 Direct Download Link", "")
                                    
                                    if download_url:
                                        if not os.path.splitext(filename)[1]:
                                            filename += ".mp4"
                                        
                                        logger.info("✅ Got file info from fallback API")
                                        return {
                                            "success": True,
                                            "filename": sanitize_filename(filename),
                                            "download_url": download_url,
                                            "file_size": 0,
                                            "fs_id": ""
                                        }
                        else:
                            logger.warning(f"API returned {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.warning("API timeout")
                    continue
                except Exception as e:
                    logger.warning(f"API error: {e}")
                    continue
            
            logger.error("All fallback methods failed")
            return {"success": False, "error": "All extraction methods failed"}
            
        except Exception as e:
            logger.error(f"Fallback method error: {e}")
            return {"success": False, "error": str(e)}

    async def get_download_link(self, surl: str, fs_id: str, page_data: dict) -> Optional[str]:
        """Get direct download link"""
        try:
            if not fs_id:
                return None
                
            session = await self.get_session()
            
            # Extract necessary tokens from page data
            bdstoken = page_data.get('bdstoken', '')
            logid = page_data.get('logid', '')
            
            # Download API endpoint
            download_api = "https://www.terabox.com/api/download"
            
            # Parameters for download request
            params = {
                'app_id': '250528',
                'web': '1',
                'channel': 'chunlei',
                'clienttype': '0',
                'fidlist': f'[{fs_id}]',
                'type': 'dlink',
                'vip': '0'
            }
            
            if bdstoken:
                params['bdstoken'] = bdstoken
            if logid:
                params['logid'] = logid
            
            logger.info("🔗 Requesting download link...")
            
            async with session.get(download_api, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('errno') == 0 and 'dlink' in result:
                        dlink_list = result['dlink']
                        if dlink_list:
                            download_url = dlink_list[0]['dlink']
                            logger.info("✅ Got download link from API")
                            return download_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting download link: {e}")
            return None

    async def download_with_resume(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Download file with resume capability and progress tracking"""
        download_path = os.path.join("/tmp", filename)
        
        try:
            session = await self.get_session()
            
            # Check if partial file exists
            resume_pos = 0
            if os.path.exists(download_path):
                resume_pos = os.path.getsize(download_path)
                logger.info(f"📂 Resuming download from {resume_pos} bytes")
            
            # Set range header for resume
            headers = self.headers.copy()
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            logger.info(f"🚀 Starting download: {filename}")
            
            async with session.get(download_url, headers=headers) as response:
                if response.status not in [200, 206]:
                    logger.error(f"Download failed with status {response.status}")
                    return None
                
                total_size = int(response.headers.get('content-length', 0))
                if resume_pos > 0:
                    total_size += resume_pos
                
                logger.info(f"📦 Total size: {get_readable_file_size(total_size)}")
                
                mode = 'ab' if resume_pos > 0 else 'wb'
                downloaded = resume_pos
                start_time = asyncio.get_event_loop().time()
                
                async with aiofiles.open(download_path, mode) as f:
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        if not chunk:
                            break
                            
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Progress callback every 20MB
                        if progress_callback and downloaded % (20 * 1024 * 1024) < self.chunk_size:
                            elapsed = asyncio.get_event_loop().time() - start_time
                            speed_mbps = (downloaded / (1024 * 1024)) / max(elapsed / 60, 0.01)
                            
                            try:
                                await progress_callback(downloaded, total_size, speed_mbps)
                            except Exception as e:
                                logger.warning(f"Progress callback error: {e}")
                
                if os.path.exists(download_path):
                    final_size = os.path.getsize(download_path)
                    elapsed = asyncio.get_event_loop().time() - start_time
                    final_speed = (final_size / (1024 * 1024)) / max(elapsed / 60, 0.01)
                    
                    logger.info(f"✅ Download complete: {get_readable_file_size(final_size)} at {final_speed:.1f} MB/min")
                    return download_path
                else:
                    logger.error("Download failed - file not created")
                    return None
                    
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """Main download method - Enhanced anasty17 approach"""
        try:
            logger.info(f"🎯 ENHANCED ANASTY17-METHOD: {url[:50]}...")
            
            # Extract surl from URL
            surl = await self.extract_surl_from_url(url)
            if not surl:
                logger.error("Could not extract surl from URL")
                return None
            
            logger.info(f"🔑 Extracted surl: {surl}")
            
            # Get file information
            file_info = await self.get_file_info(surl)
            if not file_info.get("success"):
                logger.error(f"File info extraction failed: {file_info.get('error')}")
                return None
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            
            # Download the file
            return await self.download_with_resume(download_url, filename, progress_callback)
            
        except Exception as e:
            logger.error(f"Enhanced anasty17-method download error: {e}")
            return None

    # Compatibility methods for existing code
    async def extract_file_info(self, url: str, api_index: int = 0) -> dict:
        """Compatibility method for existing code"""
        surl = await self.extract_surl_from_url(url)
        if not surl:
            return {"success": False, "error": "Could not extract surl"}
        
        return await self.get_file_info(surl)

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
