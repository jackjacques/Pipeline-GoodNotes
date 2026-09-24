import os
import io
import re
import tempfile
from typing import List, Dict, Any, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from config import config

class GoogleDriveSync:
    def __init__(self):
        self.folder_id = config.GDRIVE_FOLDER_ID
        self.creds_file = config.GOOGLE_APPLICATION_CREDENTIALS
        self.service = None
        self._init_service()

    def _init_service(self):
        if not os.path.exists(self.creds_file):
            print(f"[Warning] Google Drive credentials file missing at '{self.creds_file}'. Drive sync running in mock mode.")
            return

        try:
            scopes = ['https://www.googleapis.com/auth/drive.readonly']
            creds = service_account.Credentials.from_service_account_file(
                self.creds_file, scopes=scopes
            )
            self.service = build('drive', 'v3', credentials=creds)
            print("[GDrive] Successfully initialized Google Drive API client.")
        except Exception as e:
            print(f"[GDrive Error] Failed to initialize Google Drive API: {e}")

    def list_pdf_files(self) -> List[Dict[str, Any]]:
        """
        Recursively scans Google Drive GoodNotes folder:
        - Level 1 folder under GoodNotes root = School / École (e.g. 'TSP', 'Master BME')
        - Level 2 or Level 3 folder (inside 1A/2A/3A/Master) = Real Subject / Matière (e.g. 'IMA 4101', 'PHY - 4101')
        """
        if not self.service or not self.folder_id:
            return []

        pdf_files = []

        def _scan_folder(folder_id: str, path: List[str]):
            try:
                query = f"'{folder_id}' in parents and trashed = false"
                page_token = None
                
                while True:
                    results = None
                    for attempt in range(3):
                        try:
                            results = self.service.files().list(
                                q=query,
                                fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                                pageToken=page_token,
                                pageSize=1000
                            ).execute()
                            break
                        except Exception as req_err:
                            if attempt == 2:
                                print(f"[GDrive Warning] API request failed after 3 attempts: {req_err}")
                                results = {}
                            else:
                                import time
                                time.sleep(1.5 * (attempt + 1))
                    
                    items = results.get('files', []) if results else []
                    
                    for item in items:
                        mime_type = item.get('mimeType')
                        item_name = item.get('name')
                        item_id = item.get('id')

                        if mime_type == 'application/vnd.google-apps.folder':
                            # Skip excluded folders such as 'Perso', '1A', '2A'
                            is_excluded = (
                                item_name in config.EXCLUDED_FOLDERS 
                                or item_name.lower() in [f.lower() for f in config.EXCLUDED_FOLDERS]
                                or bool(re.search(r'\b(1a|2a)\b', item_name.lower()))
                            )
                            if is_excluded:
                                print(f"[GDrive] Skipping excluded folder: '{item_name}'")
                                continue

                            _scan_folder(item_id, path + [item_name])
                            
                        elif mime_type == 'application/pdf':
                            title = os.path.splitext(item_name)[0]
                            
                            # Strict Google Drive folder path mapping
                            school_name = path[0] if len(path) >= 1 else "TSP"
                            year_name = "2A"
                            subject_name = "Général"

                            if 'bme' in school_name.lower() or 'bme' in ' '.join(path).lower():
                                school_name = "Master BME"
                                year_name = "3A"
                                subject_name = path[1] if len(path) >= 2 else "Général"
                            else:
                                school_name = "TSP"
                                if len(path) >= 2:
                                    y_raw = path[1]
                                    if '1a' in y_raw.lower(): year_name = "1A"
                                    elif '3a' in y_raw.lower() or 'vap' in y_raw.lower(): year_name = "3A"
                                    elif '2a' in y_raw.lower(): year_name = "2A"
                                    else: year_name = y_raw
                                
                                if len(path) >= 3:
                                    subject_name = path[2]
                                elif len(path) == 2:
                                    subject_name = path[1]

                            # Filter: Only process Master BME and 3A-HTI (legacy TSP 1A/2A are ignored)
                            is_bme = (school_name == "Master BME") or ('bme' in ' '.join(path).lower())
                            is_3a_hti = (school_name == "TSP" or 'tsp' in ' '.join(path).lower()) and (
                                year_name == "3A" or 'hti' in subject_name.lower() or 'hti' in ' '.join(path).lower() or 'vap' in ' '.join(path).lower() or '3a' in ' '.join(path).lower()
                            )

                            if not (is_bme or is_3a_hti):
                                print(f"[GDrive] Skipping legacy note (non-BME, non-3A): '{item_name}' ({school_name} / {year_name})")
                                continue

                            pdf_files.append({
                                "id": item_id,
                                "name": item_name,
                                "title": title,
                                "school": school_name,
                                "year": year_name,
                                "subject": subject_name,
                                "modifiedTime": item.get('modifiedTime')
                            })

                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break

            except Exception as e:
                print(f"[GDrive Error] Error scanning folder {folder_id}: {e}")

        _scan_folder(self.folder_id, [])
        return pdf_files

    def download_file(self, file_id: str, dest_path: str) -> bool:
        """Downloads a PDF file from Google Drive to local disk."""
        if not self.service:
            return False

        try:
            request = self.service.files().get_media(fileId=file_id)
            with open(dest_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return True
        except Exception as e:
            print(f"[GDrive Error] Failed to download file {file_id}: {e}")
            return False
