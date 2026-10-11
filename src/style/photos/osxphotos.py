from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

from PIL import Image, ImageOps

DEFAULT_EXPORT_MAX_EDGE = 1600
DEFAULT_EXPORT_JPEG_QUALITY = 85
DEFAULT_EXPORT_JPEG_QUALITY_RATIO = DEFAULT_EXPORT_JPEG_QUALITY / 100.0


class Photo(Protocol):
    original_filename: str


class ExportOptions(Protocol):
    download_missing: bool
    update: bool
    convert_to_jpeg: bool
    jpeg_quality: float


class PhotoExporter(Protocol):
    def export(
        self, destination: Path, *, filename: str | None = None, options: ExportOptions
    ) -> object: ...


class PhotosDB(Protocol):
    def photos(self) -> list[Photo]: ...


class OsxPhotos(Protocol):
    def ExportOptions(
        self,
        *,
        download_missing: bool,
        update: bool,
        convert_to_jpeg: bool,
        jpeg_quality: float,
    ) -> ExportOptions: ...

    def PhotoExporter(self, photo: Photo) -> PhotoExporter: ...

    def PhotosDB(self) -> PhotosDB: ...


osxphotos: OsxPhotos | None = None


def resize_photo_to_jpeg(
    source: Path,
    *,
    max_edge: int = DEFAULT_EXPORT_MAX_EDGE,
    quality: int = DEFAULT_EXPORT_JPEG_QUALITY,
) -> Path:
    if max_edge <= 0:
        raise ValueError("max_edge must be greater than 0")
    if not 1 <= quality <= 100:
        raise ValueError("quality must be between 1 and 100")

    target = source if source.suffix.lower() in {".jpg", ".jpeg"} else source.with_suffix(".jpg")

    with Image.open(source) as image:
        converted = ImageOps.exif_transpose(image).convert("RGB")
        width, height = converted.size
        if width == 0 or height == 0:
            raise ValueError(f"Cannot resize image with zero dimensions: {source}")

        scale = min(max_edge / width, max_edge / height, 1.0)
        resized = converted
        if scale < 1.0:
            resized = converted.resize(  # pyright: ignore[reportUnknownMemberType]
                (max(1, round(width * scale)), max(1, round(height * scale))),
                Image.Resampling.LANCZOS,
            )

        resized.save(target, format="JPEG", quality=quality, optimize=True)

    if source != target:
        source.unlink(missing_ok=True)

    return target


class OsxPhotosPhotoLibrary:
    def export_by_original_filename(self, original_filename: str, destination: Path) -> int:
        destination = destination.expanduser()
        destination.mkdir(parents=True, exist_ok=True)
        photos = osxphotos or cast(OsxPhotos, import_module("osxphotos"))

        options = photos.ExportOptions(
            download_missing=True,
            update=True,
            convert_to_jpeg=True,
            jpeg_quality=DEFAULT_EXPORT_JPEG_QUALITY_RATIO,
        )
        matches = [
            photo
            for photo in photos.PhotosDB().photos()
            if photo.original_filename == original_filename
        ]

        exported_count = 0
        for photo in matches:
            base_name = Path(photo.original_filename).stem
            before_exports = sorted(destination.glob(f"{base_name}*.jpeg"))

            photos.PhotoExporter(photo).export(
                destination,
                filename=Path(photo.original_filename).with_suffix(".jpeg").name,
                options=options,
            )

            after_exports = sorted(destination.glob(f"{base_name}*.jpeg"))
            exported_paths = [
                candidate for candidate in after_exports if candidate not in before_exports
            ]
            if not exported_paths:
                continue

            exported_path = max(exported_paths, key=lambda path: path.stat().st_mtime_ns)
            resize_photo_to_jpeg(
                exported_path,
                max_edge=DEFAULT_EXPORT_MAX_EDGE,
                quality=DEFAULT_EXPORT_JPEG_QUALITY,
            )
            exported_count += 1

        return exported_count
