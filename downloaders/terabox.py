import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
from utils.helpers import sanitize_filename, get_readable_file_size

logger = logging.getLogger(__name__)

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(
                total=600,      # 10 minutes total timeout
                connect=30,     # 30 seconds to connect
                sock_read=300   # 5 minutes to read response
            )
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent},
                timeout=timeout
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
            
            # If already a direct file link, return as-is
            if "/file/" in url:
                logger.info("Direct file link detected")
                return {"single_url": url, "filename": "terabox_file.mp4"}
            
            # Use official API (same as anasty17)
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
            
            # Process API response (same logic as official)
            if "✅ Status" not in req:
                logger.error(f"❌ API Error: File not found in response. Response: {req}")
                raise Exception(f"File not found in API response! API returned: {req}")
            
            if "📜 Extracted Info" not in req:
                logger.error(f"❌ API Error: No extracted info in response. Response: {req}")
                raise Exception(f"No extracted info in API response! API returned: {req}")
                
            extracted_info = req["📜 Extracted Info"]
            logger.info(f"📊 Found {len(extracted_info)} files in API response")
            
            details = {"contents": [], "title": "", "total_size": 0}
            
            # Extract files from API response
            for i, data in enumerate(extracted_info):
                logger.info(f"🔍 Processing file {i+1}: {data.get('📂 Title', 'Unknown')}")
                
                # Preserve original filename from API
                original_filename = data.get("📂 Title", f"terabox_file_{i}")
                
                # Ensure video files have proper extension
                if not self.has_video_extension(original_filename):
                    original_filename += ".mp4"
                
                item = {
                    "path": "",
                    "filename": sanitize_filename(original_filename),
                    "url": data.get("🔽 Direct Download Link", ""),
                }
                details["contents"].append(item)
                logger.info(f"✅ Added file: {item['filename']} -> {item['url'][:50]}...")
            
            # Set folder/file title
            details["title"] = extracted_info[0].get("📂 Title", "Unknown")
            
            # Return single URL for single files, full details for folders
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
            
        except aiohttp.ClientTimeout as e:
            logger.error(f"❌ Timeout error calling Terabox API: {str(e)}")
            raise Exception(f"Terabox API timeout: {str(e)}")
        except aiohttp.ClientError as e:
            logger.error(f"❌ Network error calling Terabox API: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error extracting Terabox info: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
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
        """Download file from Terabox URL with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"🚀 Starting Terabox download (attempt {retry_count + 1}): {url}")
                
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
                
                # Download the file with retry logic
                session = await self.get_session()
                logger.info(f"🌐 Starting download from: {download_url[:100]}...")
                
                async with session.get(download_url) as response:
                    logger.info(f"📊 Download response status: {response.status}")
                    
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        logger.info(f"📦 File size: {get_readable_file_size(total_size)}")
                        
                        with open(download_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Progress callback
                                if progress_callback and total_size > 0:
                                    try:
                                        await progress_callback(downloaded, total_size, task_id)
                                    except Exception as pe:
                                        logger.warning(f"Progress callback error: {pe}")
                        
                        logger.info(f"✅ Downloaded: {filename} ({get_readable_file_size(downloaded)})")
                        return download_path
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
                    logger.warning(f"⏰ Download timeout, retrying in 10 seconds... (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(10)
                    continue
                else:
                    logger.error(f"❌ Final timeout after {max_retries} attempts: {str(e)}")
                    raise Exception(f"Download timeout after {max_retries} attempts: {str(e)}")
            except Exception as e:
                if retry_count < max_retries - 1:
                    retry_count += 1
                    logger.warning(f"❌ Download error, retrying in 5 seconds... (attempt {retry_count + 1}/{max_retries}): {str(e)}")
                    await asyncio.sleep(5)
                    continue
                else:
                    logger.error(f"❌ Terabox download error: {str(e)}")
                    logger.error(f"❌ Error type: {type(e).__name__}")
                    raise Exception(f"Download failed: {str(e)}")
        
        raise Exception("Download failed after maximum retries")
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
                
