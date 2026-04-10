from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable
import logging
import re
import tempfile

from core.profiles.vendor_cache import VendorProfileCache
from core.config import BanditConfig

logger = logging.getLogger("bandit")


@dataclass
class DataSource:
    """Describes where a piece of data came from."""
    kind: str          # "local" | "drive" | "cache"
    path: Optional[str] = None
    folder_id: Optional[str] = None
    last_synced: Optional[str] = None


@dataclass
class ResolvedDocument:
    """A document fetched from any source."""
    filename: str
    content: bytes
    mime_type: str
    source: DataSource
    vendor_name: str


@dataclass
class ResolverResult:
    """Result of resolving all data for a vendor."""
    vendor_name: str
    profile_source: DataSource
    documents: list[ResolvedDocument] = field(
        default_factory=list
    )
    drive_available: bool = False
    drive_folder_id: Optional[str] = None
    errors: list[str] = field(default_factory=list)


class VendorDataResolver:
    """
    Unified data access layer for Bandit.

    Knows where each vendor's data lives and fetches
    from the right place transparently. CLI commands
    and future UI both use this — neither needs to
    know whether data comes from local or Drive.

    Usage:
        resolver = VendorDataResolver("Cyera")
        result = resolver.resolve()
        docs = result.documents       # from wherever
        profile = resolver.profile    # latest version

    Drive resolution:
        - If Drive configured and vendor has folder_id:
          fetches directly (no search, uses stored ID)
        - If Drive unavailable: falls back to local cache
        - Sync failures are logged, never raised
    """

    def __init__(
        self,
        vendor_name: str,
        local_docs_path: Optional[Path] = None,
        on_progress: Optional[Callable] = None,
    ):
        self.vendor_name = vendor_name
        self.local_docs_path = local_docs_path
        self.on_progress = on_progress
        self._config = BanditConfig()
        self._cache = VendorProfileCache()
        self._profile = None
        self._drive = None
        self._drive_configured = False
        self._init_drive()

    def _progress(self, msg: str, **kwargs) -> None:
        """Emit progress without printing."""
        if self.on_progress:
            self.on_progress({"message": msg, **kwargs})

    def _init_drive(self) -> None:
        """Initialise Drive client if configured."""
        try:
            drive_cfg = (
                self._config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
            )
            if drive_cfg.get("enabled"):
                from core.integrations.google_drive import (
                    GoogleDriveClient
                )
                self._drive = GoogleDriveClient()
                self._drive.authenticate()
                self._drive_configured = True
        except Exception as e:
            logger.debug(f"Drive not available: {e}")

    @property
    def profile(self):
        """
        Returns vendor profile, pulling from Drive
        if newer than local cache.
        """
        if self._profile is None:
            self._profile = self._resolve_profile()
        return self._profile

    def _resolve_profile(self):
        """
        Pull latest profile from Drive if available,
        fall back to local cache.
        """
        local = self._cache.get(self.vendor_name)

        if not self._drive_configured:
            return local

        try:
            root_id = (
                self._config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
                .get("root_folder_id")
            )
            if root_id:
                self._cache.sync_from_drive(
                    self._drive, root_id
                )
                return self._cache.get(self.vendor_name)
        except Exception as e:
            logger.warning(
                f"Drive profile sync failed, "
                f"using local cache: {e}"
            )

        return local

    @property
    def drive_folder_id(self) -> Optional[str]:
        """
        Returns Drive folder ID from vendor profile.
        Already stored — no search needed.
        """
        if self.profile:
            return self.profile.drive_folder_id
        return None

    def resolve(
        self,
        include_documents: bool = True,
    ) -> ResolverResult:
        """
        Resolve all data for this vendor.
        Returns ResolverResult with profile + documents.
        """
        profile_source = DataSource(kind="local")
        errors = []
        documents = []

        # Resolve profile source
        if self._drive_configured:
            profile_source = DataSource(
                kind="drive",
                last_synced=getattr(
                    self.profile, "drive_last_synced", None
                )
            )

        if include_documents:
            # Local documents
            if self.local_docs_path:
                self._progress(
                    "Loading local documents",
                    source="local"
                )
                try:
                    local_docs = self._load_local_docs()
                    documents.extend(local_docs)
                except Exception as e:
                    errors.append(f"Local docs error: {e}")

            # Drive documents
            if (self._drive_configured
                    and self.drive_folder_id):
                self._progress(
                    "Loading Drive documents",
                    source="drive"
                )
                try:
                    drive_docs = self._load_drive_docs()
                    documents.extend(drive_docs)
                except Exception as e:
                    errors.append(f"Drive docs error: {e}")
                    logger.warning(
                        f"Drive document fetch failed: {e}"
                    )

            # Deduplicate by filename
            documents = self._deduplicate(documents)

        return ResolverResult(
            vendor_name=self.vendor_name,
            profile_source=profile_source,
            documents=documents,
            drive_available=self._drive_configured,
            drive_folder_id=self.drive_folder_id,
            errors=errors,
        )

    # Matches date suffix in report filenames: YYYY-MM-DD
    _REPORT_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

    def _should_skip_doc(self, name: str) -> bool:
        """
        Return True for files that are Bandit-generated
        reports or other non-vendor-policy documents.
        Excludes: HTML files, report HTML, legal briefs,
        and any file whose name contains a YYYY-MM-DD date.
        """
        lower = name.lower()
        if lower.endswith(".html"):
            return True
        if "privacy-assessment" in lower:
            return True
        if "-legal" in lower:
            return True
        if self._REPORT_DATE_RE.search(name):
            return True
        return False

    def _load_local_docs(self) -> list[ResolvedDocument]:
        """Load documents from local path."""
        docs = []
        if not self.local_docs_path:
            return docs

        path = Path(self.local_docs_path)
        if not path.exists():
            return docs

        source = DataSource(
            kind="local",
            path=str(path)
        )

        for f in path.iterdir():
            if not f.is_file():
                continue
            if self._should_skip_doc(f.name):
                logger.debug(f"Skipping report file: {f.name}")
                continue
            if f.suffix.lower() in (
                ".pdf", ".docx", ".doc", ".txt", ".json"
            ):
                try:
                    docs.append(ResolvedDocument(
                        filename=f.name,
                        content=f.read_bytes(),
                        mime_type=self._mime(f.suffix),
                        source=source,
                        vendor_name=self.vendor_name,
                    ))
                except Exception as e:
                    logger.warning(
                        f"Could not read {f.name}: {e}"
                    )
        return docs

    def _load_drive_docs(self) -> list[ResolvedDocument]:
        """Load documents from Drive folder."""
        if not self._drive or not self.drive_folder_id:
            return []

        docs = []
        source = DataSource(
            kind="drive",
            folder_id=self.drive_folder_id
        )

        try:
            files = self._drive.list_vendor_files(
                self.drive_folder_id
            )
            for f in files:
                # Skip report and generated files
                if self._should_skip_doc(f["name"]):
                    logger.debug(
                        f"Skipping report file: {f['name']}"
                    )
                    continue
                try:
                    with tempfile.TemporaryDirectory() as tmp:
                        local_path = self._drive.download_file(
                            f["id"], f["name"], tmp
                        )
                        content = Path(local_path).read_bytes()
                    docs.append(ResolvedDocument(
                        filename=f["name"],
                        content=content,
                        mime_type=f.get(
                            "mimeType", "application/octet-stream"
                        ),
                        source=source,
                        vendor_name=self.vendor_name,
                    ))
                except Exception as e:
                    logger.warning(
                        f"Could not download "
                        f"{f['name']}: {e}"
                    )
        except Exception as e:
            logger.warning(
                f"Could not list Drive folder "
                f"{self.drive_folder_id}: {e}"
            )
        return docs

    def save_report(
        self,
        report_path: Path,
        also_save_to_drive: bool = True,
    ) -> None:
        """
        Save a completed report locally and optionally
        to Drive vendor folder.
        """
        # Drive save
        if (also_save_to_drive
                and self._drive_configured
                and self.drive_folder_id):
            try:
                self._drive.upload_file(
                    file_path=report_path,
                    folder_id=self.drive_folder_id,
                    file_name=report_path.name,
                )
            except Exception as e:
                logger.warning(
                    f"Could not save report to Drive: {e}"
                )

    def sync_profile_to_drive(self) -> bool:
        """
        Push updated local profile to Drive.
        Returns True if successful.
        """
        if not self._drive_configured:
            return False

        try:
            root_id = (
                self._config.get_profile()
                .get("integrations", {})
                .get("google_drive", {})
                .get("root_folder_id")
            )
            if root_id:
                return self._cache.sync_to_drive(
                    self._drive, root_id
                )
        except Exception as e:
            logger.warning(
                f"Profile Drive sync failed: {e}"
            )
        return False

    def _deduplicate(
        self,
        docs: list[ResolvedDocument]
    ) -> list[ResolvedDocument]:
        """
        Remove duplicate documents by filename.
        Drive version wins over local when both exist.
        """
        seen = {}
        for doc in docs:
            existing = seen.get(doc.filename)
            if not existing:
                seen[doc.filename] = doc
            elif doc.source.kind == "drive":
                seen[doc.filename] = doc
        return list(seen.values())

    @staticmethod
    def _mime(suffix: str) -> str:
        return {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-"
                     "officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".json": "application/json",
            ".html": "text/html",
        }.get(suffix.lower(), "application/octet-stream")


def get_all_vendor_resolvers(
    on_progress: Optional[Callable] = None,
) -> list[VendorDataResolver]:
    """
    Returns a resolver for every vendor in the
    local profile cache. Used by dashboard/schedule.
    """
    cache = VendorProfileCache()
    profiles = cache.list_all()
    return [
        VendorDataResolver(
            p.vendor_name,
            on_progress=on_progress
        )
        for p in profiles
    ]
