"""
Bandit Google Drive Integration
================================
Full OAuth 2.0 client for reading vendor documents from Google Drive
and saving HTML reports back to vendor folders.

Authentication:
  Credentials: ~/.bandit/google-credentials.json (OAuth client secrets)
  Token:       ~/.bandit/google-token.json        (refreshable token)

Scopes:
  https://www.googleapis.com/auth/drive
  (read.readonly is insufficient — saving reports requires write access)

Install:
  pip install -e ".[drive]"
"""
from __future__ import annotations

import io
from pathlib import Path


class GoogleDriveClient:

    SCOPES = ["https://www.googleapis.com/auth/drive"]
    CREDS_PATH = Path.home() / ".bandit" / "google-credentials.json"
    TOKEN_PATH = Path.home() / ".bandit" / "google-token.json"

    def __init__(self):
        self.service = None

    def authenticate(self) -> bool:
        """Authenticate with Google Drive. Returns True if successful."""
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None

        if self.TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(
                str(self.TOKEN_PATH), self.SCOPES
            )
            # If the stored token was granted narrower scopes than required
            # (e.g. drive.readonly → drive), discard it and re-auth.
            _granted = set(getattr(creds, "granted_scopes", None) or [])
            _required = set(self.SCOPES)
            if _granted and not _required.issubset(_granted):
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.CREDS_PATH.exists():
                    raise FileNotFoundError(
                        "Google credentials not found. "
                        "Run: bandit setup --drive"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.CREDS_PATH), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            self.TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.TOKEN_PATH.write_text(creds.to_json())

        self.service = build("drive", "v3", credentials=creds)
        return True

    def list_vendor_folders(self, parent_folder_id: str) -> list[dict]:
        """List all subfolders in the Bandit root folder."""
        results = self.service.files().list(
            q=(
                f"'{parent_folder_id}' in parents "
                f"and mimeType = 'application/vnd.google-apps.folder' "
                f"and trashed = false"
            ),
            fields="files(id, name, modifiedTime)",
            pageSize=500,
        ).execute()
        return results.get("files", [])

    def list_vendor_files(self, vendor_folder_id: str) -> list[dict]:
        """List all files in a vendor folder."""
        results = self.service.files().list(
            q=(
                f"'{vendor_folder_id}' in parents "
                f"and trashed = false"
            ),
            fields="files(id, name, mimeType, size, modifiedTime)",
            pageSize=100,
        ).execute()
        return results.get("files", [])

    def download_file(
        self,
        file_id: str,
        file_name: str,
        dest_folder: str,
    ) -> str:
        """Download a file from Drive to local folder. Returns local file path."""
        from googleapiclient.http import MediaIoBaseDownload

        dest = Path(dest_folder) / file_name
        dest.parent.mkdir(parents=True, exist_ok=True)

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        dest.write_bytes(fh.getvalue())
        return str(dest)

    def find_vendor_folder(
        self,
        vendor_name: str,
        parent_folder_id: str,
    ) -> str | None:
        """Find a vendor's folder by name. Case-insensitive, with partial match fallback."""
        folders = self.list_vendor_folders(parent_folder_id)
        vendor_lower = vendor_name.lower().strip()

        for folder in folders:
            if folder["name"].lower().strip() == vendor_lower:
                return folder["id"]

        for folder in folders:
            if vendor_lower in folder["name"].lower():
                return folder["id"]

        return None

    def download_vendor_documents(
        self,
        vendor_name: str,
        parent_folder_id: str,
        temp_dir: str,
    ) -> list[str]:
        """Find and download all documents for a vendor. Returns local file paths."""
        folder_id = self.find_vendor_folder(vendor_name, parent_folder_id)
        if not folder_id:
            return []

        files = self.list_vendor_files(folder_id)
        local_paths = []

        SUPPORTED_MIMES = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/html",
            "text/plain",
            "application/json",
        }

        for file in files:
            mime = file.get("mimeType", "")
            try:
                if mime == "application/vnd.google-apps.document":
                    local_path = self._export_google_doc(
                        file["id"], file["name"] + ".docx", temp_dir
                    )
                elif mime in SUPPORTED_MIMES:
                    local_path = self.download_file(
                        file["id"], file["name"], temp_dir
                    )
                else:
                    continue
                if local_path:
                    local_paths.append(local_path)
            except Exception:
                continue

        return local_paths

    def _export_google_doc(
        self,
        file_id: str,
        file_name: str,
        dest_folder: str,
    ) -> str:
        """Export a Google Doc as DOCX."""
        from googleapiclient.http import MediaIoBaseDownload

        dest = Path(dest_folder) / file_name
        dest.parent.mkdir(parents=True, exist_ok=True)

        request = self.service.files().export_media(
            fileId=file_id,
            mimeType=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
        )
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        dest.write_bytes(fh.getvalue())
        return str(dest)

    def save_report_to_drive(
        self,
        local_file_path: str,
        vendor_name: str,
        parent_folder_id: str,
    ) -> str | None:
        """Save HTML report back to vendor's Drive folder. Returns Drive file ID."""
        from googleapiclient.http import MediaFileUpload

        folder_id = self.find_vendor_folder(vendor_name, parent_folder_id)
        if not folder_id:
            return None

        file_metadata = {
            "name": Path(local_file_path).name,
            "parents": [folder_id],
        }
        media = MediaFileUpload(local_file_path, mimetype="text/html")
        result = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()
        return result.get("id")
