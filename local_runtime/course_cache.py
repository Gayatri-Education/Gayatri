"""Local Course Package Cache subsystem.

Provides deterministic course package caching, SHA-256 validation,
quarantine isolation for corrupted packages, and offline export/import.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from local_runtime.errors import CorruptedCacheError, OfflineCourseNotCachedError

logger = logging.getLogger("gayatri.local_runtime.course_cache")


@dataclass
class CoursePackageMetadata:
    """Authoritative metadata for a cached course package."""
    course_id: str
    version_tag: str
    title: str = ""
    checksum: str = ""
    created_at: str = ""
    total_concepts: int = 0
    file_count: int = 0
    is_valid: bool = True
    manifest: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def calculate_sha256(data: bytes | Path) -> str:
    """Calculate SHA-256 hex digest for bytes or a file path."""
    hasher = hashlib.sha256()
    if isinstance(data, Path) or (isinstance(data, str) and os.path.exists(data)):
        with open(data, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
    else:
        if isinstance(data, str):
            data = data.encode("utf-8")
        hasher.update(data)
    return hasher.hexdigest()


class LocalCourseCache:
    """Manages locally cached course bundles and offline package quarantine."""

    def __init__(
        self,
        cache_dir: Optional[Path | str] = None,
        quarantine_dir: Optional[Path | str] = None,
    ) -> None:
        self.cache_dir = Path(cache_dir or "data/cache/courses").resolve()
        self.quarantine_dir = Path(quarantine_dir or "data/cache/quarantine").resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def is_course_cached(self, course_id: str, version_tag: Optional[str] = None) -> bool:
        """Check if a course (and specific version) exists in the valid cache."""
        course_root = self.cache_dir / course_id
        if not course_root.is_dir():
            return False

        if version_tag:
            ver_dir = course_root / version_tag
            manifest_file = ver_dir / "manifest.json"
            return ver_dir.is_dir() and manifest_file.is_file()

        # Check for any valid version directory containing manifest.json
        for sub in course_root.iterdir():
            if sub.is_dir() and (sub / "manifest.json").is_file():
                return True
        return False

    def list_cached_courses(self) -> List[CoursePackageMetadata]:
        """List all valid cached courses across all versions."""
        packages: List[CoursePackageMetadata] = []
        if not self.cache_dir.exists():
            return packages

        for course_dir in self.cache_dir.iterdir():
            if not course_dir.is_dir():
                continue
            for ver_dir in course_dir.iterdir():
                if not ver_dir.is_dir():
                    continue
                manifest_file = ver_dir / "manifest.json"
                if not manifest_file.is_file():
                    continue
                try:
                    data = json.loads(manifest_file.read_text(encoding="utf-8"))
                    meta = CoursePackageMetadata(
                        course_id=data.get("course_id", course_dir.name),
                        version_tag=data.get("version_tag", ver_dir.name),
                        title=data.get("title", data.get("course_id", course_dir.name)),
                        checksum=data.get("checksum", ""),
                        created_at=data.get("created_at", ""),
                        total_concepts=data.get("total_concepts", len(data.get("concepts", []))),
                        file_count=len(list(ver_dir.glob("**/*"))),
                        is_valid=True,
                        manifest=data,
                    )
                    packages.append(meta)
                except Exception as exc:
                    logger.warning("Failed to parse manifest in %s: %s", ver_dir, exc)
        return packages

    def get_cached_course(
        self,
        course_id: str,
        version_tag: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve course package data (manifest, curriculum, knowledge)."""
        course_root = self.cache_dir / course_id
        if not course_root.is_dir():
            return None

        target_ver_dir: Optional[Path] = None
        if version_tag:
            cand = course_root / version_tag
            if cand.is_dir() and (cand / "manifest.json").is_file():
                target_ver_dir = cand
        else:
            # Pick latest or first valid version
            versions = sorted([d for d in course_root.iterdir() if d.is_dir() and (d / "manifest.json").is_file()])
            if versions:
                target_ver_dir = versions[-1]

        if not target_ver_dir:
            return None

        manifest_path = target_ver_dir / "manifest.json"
        try:
            content = json.loads(manifest_path.read_text(encoding="utf-8"))
            # If separate curriculum file exists, load it
            curriculum_path = target_ver_dir / "curriculum.json"
            if curriculum_path.is_file():
                try:
                    content["curriculum"] = json.loads(curriculum_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            return content
        except Exception as exc:
            logger.error("Failed to read cached course %s: %s", course_id, exc)
            return None

    def import_package(self, package_path: Path | str) -> CoursePackageMetadata:
        """Import a course package archive (.gpk, .zip) or JSON manifest into cache.
        
        Validates SHA-256 checksum and schema. Quarantines corrupted or tampered files.
        """
        pkg = Path(package_path).resolve()
        if not pkg.exists():
            raise FileNotFoundError(f"Package file does not exist: {pkg}")

        # Check if it's a zip archive
        if zipfile.is_zipfile(pkg):
            return self._import_zip_package(pkg)

        # Check if it's a JSON manifest
        if pkg.suffix.lower() == ".json":
            return self._import_json_package(pkg)

        # Check if it's a directory
        if pkg.is_dir():
            manifest_path = pkg / "manifest.json"
            if manifest_path.is_file():
                return self._import_json_package(manifest_path, source_dir=pkg)

        # Unrecognized format -> quarantine
        q_path = self._quarantine_file(pkg, "unsupported_package_format")
        raise CorruptedCacheError(
            course_id=pkg.stem,
            package_path=str(pkg),
            quarantine_path=str(q_path),
            reason="Unsupported package format (expected .gpk, .zip, or .json manifest)",
        )

    def _import_zip_package(self, zip_path: Path) -> CoursePackageMetadata:
        """Import and validate a zip-based .gpk bundle."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Test archive integrity
                bad_file = zf.testzip()
                if bad_file:
                    q_path = self._quarantine_file(zip_path, f"crc_failure_in_{bad_file}")
                    raise CorruptedCacheError(
                        course_id=zip_path.stem,
                        package_path=str(zip_path),
                        quarantine_path=str(q_path),
                        reason=f"CRC check failed for '{bad_file}' inside archive",
                    )

                namelist = zf.namelist()
                if "manifest.json" not in namelist:
                    q_path = self._quarantine_file(zip_path, "missing_manifest_json")
                    raise CorruptedCacheError(
                        course_id=zip_path.stem,
                        package_path=str(zip_path),
                        quarantine_path=str(q_path),
                        reason="Archive is missing required 'manifest.json'",
                    )

                manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
        except (zipfile.BadZipFile, json.JSONDecodeError) as exc:
            q_path = self._quarantine_file(zip_path, "malformed_zip_or_json")
            raise CorruptedCacheError(
                course_id=zip_path.stem,
                package_path=str(zip_path),
                quarantine_path=str(q_path),
                reason=f"Failed to open or decode archive: {exc}",
            )

        course_id = manifest_data.get("course_id")
        if not course_id:
            q_path = self._quarantine_file(zip_path, "missing_course_id_in_manifest")
            raise CorruptedCacheError(
                course_id=zip_path.stem,
                package_path=str(zip_path),
                quarantine_path=str(q_path),
                reason="Manifest does not define 'course_id'",
            )

        version_tag = manifest_data.get("version_tag", "v1.0")

        # Verify expected checksum if specified in manifest
        expected_checksum = manifest_data.get("checksum")
        if expected_checksum:
            # If payload checksum is provided, check curriculum or zip
            actual_checksum = calculate_sha256(zip_path)
            if expected_checksum != actual_checksum:
                q_path = self._quarantine_file(zip_path, "checksum_mismatch")
                raise CorruptedCacheError(
                    course_id=course_id,
                    package_path=str(zip_path),
                    quarantine_path=str(q_path),
                    reason=f"Checksum mismatch: expected '{expected_checksum}', got '{actual_checksum}'",
                )
        else:
            actual_checksum = calculate_sha256(zip_path)
            manifest_data["checksum"] = actual_checksum

        # Extract to target cache directory
        target_dir = self.cache_dir / course_id / version_tag
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(target_dir)

        # Update manifest on disk with valid checksum
        (target_dir / "manifest.json").write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        total_concepts = len(manifest_data.get("concepts", []))
        if total_concepts == 0 and (target_dir / "curriculum.json").is_file():
            try:
                curr = json.loads((target_dir / "curriculum.json").read_text(encoding="utf-8"))
                total_concepts = len(curr.get("concepts", []))
            except Exception:
                pass

        return CoursePackageMetadata(
            course_id=course_id,
            version_tag=version_tag,
            title=manifest_data.get("title", course_id),
            checksum=actual_checksum,
            created_at=manifest_data.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            total_concepts=total_concepts,
            file_count=len(list(target_dir.glob("**/*"))),
            is_valid=True,
            manifest=manifest_data,
        )

    def _import_json_package(self, json_path: Path, source_dir: Optional[Path] = None) -> CoursePackageMetadata:
        """Import a JSON-based course manifest or directory."""
        try:
            content = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            q_path = self._quarantine_file(json_path, "malformed_json")
            raise CorruptedCacheError(
                course_id=json_path.stem,
                package_path=str(json_path),
                quarantine_path=str(q_path),
                reason=f"Invalid JSON in manifest: {exc}",
            )

        course_id = content.get("course_id") or content.get("id") or content.get("subject", "").lower().replace(" ", "_")
        if not course_id:
            q_path = self._quarantine_file(json_path, "missing_course_id")
            raise CorruptedCacheError(
                course_id=json_path.stem,
                package_path=str(json_path),
                quarantine_path=str(q_path),
                reason="JSON manifest lacks course identifier ('course_id' or 'id')",
            )

        version_tag = content.get("version_tag", "v1.0")
        actual_checksum = calculate_sha256(json_path)

        expected_checksum = content.get("checksum")
        if expected_checksum and expected_checksum != actual_checksum:
            q_path = self._quarantine_file(json_path, "checksum_mismatch")
            raise CorruptedCacheError(
                course_id=course_id,
                package_path=str(json_path),
                quarantine_path=str(q_path),
                reason=f"Checksum mismatch: expected '{expected_checksum}', got '{actual_checksum}'",
            )

        content["course_id"] = course_id
        content["version_tag"] = version_tag
        content["checksum"] = actual_checksum
        content.setdefault("title", content.get("subject", course_id))

        target_dir = self.cache_dir / course_id / version_tag
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        if source_dir and source_dir.is_dir():
            for item in source_dir.iterdir():
                if item.name != "manifest.json":
                    dest = target_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)

        (target_dir / "manifest.json").write_text(json.dumps(content, indent=2), encoding="utf-8")

        return CoursePackageMetadata(
            course_id=course_id,
            version_tag=version_tag,
            title=content.get("title", course_id),
            checksum=actual_checksum,
            created_at=content.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            total_concepts=len(content.get("concepts", [])),
            file_count=len(list(target_dir.glob("**/*"))),
            is_valid=True,
            manifest=content,
        )

    def export_package(
        self,
        course_id: str,
        version_tag: Optional[str] = None,
        target_path: Optional[Path | str] = None,
    ) -> Path:
        """Export a cached course into a distributable .gpk zip bundle."""
        course_root = self.cache_dir / course_id
        if not course_root.is_dir():
            raise OfflineCourseNotCachedError(course_id=course_id)

        target_ver_dir: Optional[Path] = None
        if version_tag:
            cand = course_root / version_tag
            if cand.is_dir():
                target_ver_dir = cand
        else:
            versions = sorted([d for d in course_root.iterdir() if d.is_dir()])
            if versions:
                target_ver_dir = versions[-1]

        if not target_ver_dir or not (target_ver_dir / "manifest.json").is_file():
            raise OfflineCourseNotCachedError(course_id=course_id, version_tag=version_tag)

        actual_ver = target_ver_dir.name
        out_file = Path(target_path or f"{course_id}_{actual_ver}.gpk").resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(target_ver_dir):
                for f in files:
                    full_f = Path(root) / f
                    arcname = full_f.relative_to(target_ver_dir)
                    zf.write(full_f, arcname=str(arcname))

        return out_file

    def quarantine_course(
        self,
        course_id: str,
        reason: str = "Manual quarantine",
        version_tag: Optional[str] = None,
    ) -> Path:
        """Move a course or version directory to the quarantine repository."""
        source_dir = self.cache_dir / course_id
        if version_tag:
            source_dir = source_dir / version_tag

        if not source_dir.exists():
            raise OfflineCourseNotCachedError(course_id=course_id, version_tag=version_tag)

        timestamp = int(time.time())
        dest_name = f"quarantine_{timestamp}_{course_id}_{version_tag or 'all'}"
        dest_dir = self.quarantine_dir / dest_name

        shutil.move(str(source_dir), str(dest_dir))
        # Record quarantine metadata
        q_meta = {
            "course_id": course_id,
            "version_tag": version_tag,
            "reason": reason,
            "quarantined_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (dest_dir / "quarantine_info.json").write_text(json.dumps(q_meta, indent=2), encoding="utf-8")
        return dest_dir

    def _quarantine_file(self, file_path: Path, reason_suffix: str) -> Path:
        """Quarantine a corrupted file by moving or copying to the quarantine directory."""
        timestamp = int(time.time())
        dest_name = f"corrupted_{timestamp}_{reason_suffix}_{file_path.name}"
        dest_path = self.quarantine_dir / dest_name
        try:
            shutil.copy2(str(file_path), str(dest_path))
        except Exception:
            pass
        return dest_path
