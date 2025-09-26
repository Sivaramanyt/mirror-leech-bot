import asyncio
import logging
import os
import pickle
from typing import Optional, Dict
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceCredentials
from googleapiclient.http import MediaFileUpload
import config

logger = logging.getLogger(__name__)

class GDriveHandler:
    def __init__(self, bot):
        self.bot = bot
        self.service = None

    async def initialize(self):
        """Initialize Google Drive service"""
        try:
            loop = asyncio.get_event_loop()

            def build_service():
                # Try service accounts first
                if config.USE_SERVICE_ACCOUNTS and os.path.exists('accounts'):
                    try:
                        account_files = [f for f in os.listdir('accounts') if f.endswith('.json')]
                        if account_files:
                            account_path = os.path.join('accounts', account_files[0])
                            creds = ServiceCredentials.from_service_account_file(
                                account_path, 
                                scopes=['https://www.googleapis.com/auth/drive']
                            )
                            return build('drive', 'v3', credentials=creds)
                    except Exception as e:
                        logger.error(f"Service account error: {e}")

                # Try token.pickle
                if os.path.exists('token.pickle'):
                    try:
                        with open('token.pickle', 'rb') as token:
                            creds = pickle.load(token)

                        if creds and creds.expired and creds.refresh_token:
                            creds.refresh(Request())

                        return build('drive', 'v3', credentials=creds)
                    except Exception as e:
                        logger.error(f"Token pickle error: {e}")

                return None

            self.service = await loop.run_in_executor(None, build_service)

            if self.service:
                logger.info("✅ Google Drive service initialized")
                return True
            else:
                logger.error("❌ Failed to initialize Google Drive service")
                return False

        except Exception as e:
            logger.error(f"GDrive initialization error: {e}")
            return False

    async def upload_file(self, file_path: str, parent_id: str = None) -> Optional[Dict]:
        """Upload file to Google Drive"""
        try:
            if not self.service:
                if not await self.initialize():
                    return None

            filename = os.path.basename(file_path)

            # File metadata
            file_metadata = {
                'name': filename,
                'parents': [parent_id or config.GDRIVE_ID] if (parent_id or config.GDRIVE_ID) else []
            }

            # Create media upload
            media = MediaFileUpload(
                file_path,
                resumable=True,
                chunksize=8192 * 1024  # 8MB chunks
            )

            loop = asyncio.get_event_loop()

            def do_upload():
                request = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    supportsAllDrives=config.IS_TEAM_DRIVE
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        # Progress can be tracked here if needed
                        pass

                return response

            result = await loop.run_in_executor(None, do_upload)

            if result:
                file_id = result.get('id')

                # Make file publicly viewable
                await loop.run_in_executor(
                    None,
                    self._make_public,
                    file_id
                )

                # Generate download link
                download_link = f"https://drive.google.com/file/d/{file_id}/view"

                logger.info(f"✅ Uploaded to GDrive: {filename}")

                return {
                    'id': file_id,
                    'name': filename,
                    'link': download_link,
                    'size': os.path.getsize(file_path)
                }

            return None

        except Exception as e:
            logger.error(f"GDrive upload error: {e}")
            return None

    def _make_public(self, file_id: str):
        """Make file publicly viewable"""
        try:
            self.service.permissions().create(
                fileId=file_id,
                body={
                    'role': 'reader',
                    'type': 'anyone'
                },
                supportsAllDrives=config.IS_TEAM_DRIVE
            ).execute()
        except Exception as e:
            logger.error(f"Error making file public: {e}")

    async def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file information"""
        try:
            if not self.service:
                if not await self.initialize():
                    return None

            loop = asyncio.get_event_loop()

            def get_info():
                return self.service.files().get(
                    fileId=file_id,
                    fields='id,name,size,mimeType,createdTime',
                    supportsAllDrives=config.IS_TEAM_DRIVE
                ).execute()

            result = await loop.run_in_executor(None, get_info)
            return result

        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

    async def delete_file(self, file_id: str) -> bool:
        """Delete file from Google Drive"""
        try:
            if not self.service:
                if not await self.initialize():
                    return False

            loop = asyncio.get_event_loop()

            def delete():
                return self.service.files().delete(
                    fileId=file_id,
                    supportsAllDrives=config.IS_TEAM_DRIVE
                ).execute()

            await loop.run_in_executor(None, delete)
            logger.info(f"✅ Deleted file from GDrive: {file_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
