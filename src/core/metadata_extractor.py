"""
Metadata extraction from various file formats.

Extracts EXIF, XMP, IPTC, and technical metadata from images, videos, and documents.
"""

import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import exifread
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    exifread = None
    Image = None
    TAGS = None


class MetadataExtractor:
    """Extract metadata from media files."""

    def __init__(self):
        """Initialize metadata extractor."""
        self.supported_formats = {
            "image/jpeg",
            "image/png",
            "image/tiff",
            "image/webp",
            "application/pdf",
        }

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing extracted metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        mime_type = self._get_mime_type(file_path)
        metadata: Dict[str, Any] = {
            "file_name": path.name,
            "file_size": path.stat().st_size,
            "mime_type": mime_type,
            "file_modified": datetime.fromtimestamp(path.stat().st_mtime),
        }

        if mime_type.startswith("image/"):
            metadata.update(self._extract_image_metadata(file_path))
        elif mime_type == "application/pdf":
            metadata.update(self._extract_pdf_metadata(file_path))

        return metadata

    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from image files."""
        metadata: Dict[str, Any] = {}

        if Image is None:
            return metadata

        try:
            with Image.open(file_path) as img:
                metadata["width"] = img.width
                metadata["height"] = img.height
                metadata["format"] = img.format
                metadata["mode"] = img.mode

                # Extract EXIF data
                exif_data = img._getexif()
                if exif_data:
                    exif_dict = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if isinstance(value, bytes):
                            try:
                                value = value.decode("utf-8")
                            except UnicodeDecodeError:
                                value = str(value)
                        exif_dict[tag] = value
                    metadata["exif"] = exif_dict

                    # Extract key EXIF fields
                    if "DateTime" in exif_dict:
                        try:
                            metadata["date_created"] = datetime.strptime(
                                exif_dict["DateTime"], "%Y:%m:%d %H:%M:%S"
                            )
                        except (ValueError, TypeError):
                            pass

                    if "Make" in exif_dict:
                        metadata["camera_make"] = exif_dict["Make"]
                    if "Model" in exif_dict:
                        metadata["camera_model"] = exif_dict["Model"]
                    if "Software" in exif_dict:
                        metadata["software"] = exif_dict["Software"]
                    if "Artist" in exif_dict:
                        metadata["artist"] = exif_dict["Artist"]
                    if "Copyright" in exif_dict:
                        metadata["copyright"] = exif_dict["Copyright"]

        except Exception as e:
            metadata["extraction_error"] = str(e)

        return metadata

    def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF files."""
        metadata: Dict[str, Any] = {}

        try:
            from PyPDF2 import PdfReader

            with open(file_path, "rb") as f:
                pdf = PdfReader(f)
                info = pdf.metadata

                if info:
                    if info.title:
                        metadata["title"] = info.title
                    if info.author:
                        metadata["author"] = info.author
                    if info.creator:
                        metadata["creator"] = info.creator
                    if info.producer:
                        metadata["producer"] = info.producer
                    if info.subject:
                        metadata["subject"] = info.subject
                    if info.creation_date:
                        metadata["creation_date"] = info.creation_date

                metadata["num_pages"] = len(pdf.pages)

        except ImportError:
            metadata["extraction_error"] = "PyPDF2 not installed"
        except Exception as e:
            metadata["extraction_error"] = str(e)

        return metadata

    def extract_gps_location(self, file_path: str) -> Optional[Dict[str, float]]:
        """
        Extract GPS coordinates from image EXIF data.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with latitude and longitude, or None
        """
        if Image is None:
            return None

        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if not exif_data:
                    return None

                gps_info = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "GPSInfo":
                        for gps_tag_id, gps_value in value.items():
                            gps_tag = TAGS.get(gps_tag_id, gps_tag_id)
                            gps_info[gps_tag] = gps_value

                if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                    lat = self._convert_gps_to_decimal(
                        gps_info["GPSLatitude"], gps_info.get("GPSLatitudeRef", "N")
                    )
                    lon = self._convert_gps_to_decimal(
                        gps_info["GPSLongitude"], gps_info.get("GPSLongitudeRef", "E")
                    )
                    return {"latitude": lat, "longitude": lon}

        except Exception:
            pass

        return None

    def _convert_gps_to_decimal(self, gps_coords: tuple, ref: str) -> float:
        """Convert GPS coordinates to decimal format."""
        degrees = float(gps_coords[0])
        minutes = float(gps_coords[1])
        seconds = float(gps_coords[2])

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        if ref in ["S", "W"]:
            decimal = -decimal

        return decimal
