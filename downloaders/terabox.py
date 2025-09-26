import asyncio
import aiohttp
import re
import json
import logging
from typing import Optional, Callable
from utils.helpers import sanitize_filename, get_readable_file_size

logger = logging.getLogger(__name__)

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    async def create_session(self):
        """Create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=3600)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def extract_download_link(self, share_url: str) -> Optional[dict]:
        """Extract direct download link from Terabox share URL"""
        try:
            await self.create_session()
            
            # Get the share page
            async with self.session.get(share_url, allow_redirects=True) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch share page: {response.status}")
                    return None
                
                content = await response.text()
            
            # Extract file information using regex patterns - FIXED SYNTAX
            patterns = {
                'app_id': r'window\.yunData\.APPID\s*=\s*["\']?(\d+)["\']?',
                'uk': r'window\.yunData\.SHARE_UK\s*=\s*["\']?(\d+)["\']?',
                'shareid': r'window\.yunData\.SHAREID\s*=\s*["\']?(\d+)["\']?',
                'sign': r'window\.yunData\.SIGN\s*=\s*["\']([^"\']*)["\']',
                'timestamp': r'window\.yunData\.TIMESTAMP\s*=\s*["\']?(\d+)["\']?'
            }
            
            extracted_data = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    extracted_data[key] = match.group(1)
            
            # Extract file list
            file_list_pattern = r'window\.yunData\.setData\s*\(\s*({.*?})\s*\)'
            file_list_match = re.search(file_list_pattern, content, re.DOTALL)
            if file_list_match:
                try:
                    data = json.loads(file_list_match.group(1))
                    file_list = data.get('file_list', [])
                    if file_list:
                        return {
                            'file_info': file_list[0],
                            'extracted_data': extracted_data,
                            'share_url': share_url
                        }
                except json.JSONDecodeError:
                    pass
            
            # Fallback API method
            if extracted_data.get('shareid') and extracted_data.get('uk'):
                return await self.get_file_info_api(extracted_data, share_url)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting download link: {e}")
            return None
    
    async def get_file_info_api(self, data: dict, share_url: str) -> Optional[dict]:
        """Get file info using Terabox API"""
        try:
            api_url = "https://www.terabox.com/share/list"
            params = {
                'app_id': data.get('app_id', '250528'),
                'channel': 'dubox',
                'clienttype': '0',
                'desc': '1',
                'num': '20',
                'order': 'time',
                'page': '1',
                'root': '1',
                'shareid': data.get('shareid'),
                'sign': data.get('sign', ''),
                'timestamp': data.get('timestamp', ''),
                'uk': data.get('uk'),
                'web': '1'
            }
            
            async with self.session.get(api_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get('errno') == 0 and result.get('list'):
                        return {
                            'file_info': result['list'][0],
                            'extracted_data': data,
                            'share_url': share_url
                        }
            return None
                    
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None
    
    async def get_download_url(self, file_data: dict) -> Optional[str]:
        """Get direct download URL"""
        try:
            file_info = file_data['file_info']
            
            # Check for direct link
            if 'dlink' in file_info and file_info['dlink']:
                return file_info['dlink']
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting download URL: {e}")
            return None
    
    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """Download file from Terabox"""
        try:
            file_data = await self.extract_download_link(url)
            if not file_data:
                return None
            
            download_url = await self.get_download_url(file_data)
            if not download_url:
                return None
            
            file_info = file_data['file_info']
            filename = sanitize_filename(file_info.get('server_filename', 'terabox_file'))
            file_size = int(file_info.get('size', 0))
            
            import os
            os.makedirs('/tmp/downloads', exist_ok=True)
            file_path = f'/tmp/downloads/{filename}'
            
            downloaded = 0
            async with self.session.get(download_url) as response:
                if response.status != 200:
                    return None
                
                with open(file_path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        file.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and task_id:
                            await progress_callback(downloaded, file_size, task_id)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
        finally:
            await self.close_session()
    
    async def get_file_info(self, url: str) -> Optional[dict]:
        """Get file information without downloading"""
        try:
            file_data = await self.extract_download_link(url)
            if file_data:
                file_info = file_data['file_info']
                return {
                    'title': file_info.get('server_filename', 'Unknown'),
                    'size': int(file_info.get('size', 0)),
                    'type': file_info.get('category', 'file')
                }
            return None
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
            
