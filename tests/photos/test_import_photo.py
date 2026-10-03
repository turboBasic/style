from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

from style.photos.import_photo import ImportPhotoService, PhotoNotFoundError
from style.photos.osxphotos import OsxPhotosPhotoLibrary, resize_photo_to_jpeg


class FakePhotoLibrary:
    def __init__(self, exported_count: int) -> None:
        self.exported_count = exported_count
        self.calls: list[tuple[str, Path]] = []

    def export_by_original_filename(self, original_filename: str, destination: Path) -> int:
        self.calls.append((original_filename, destination))
        return self.exported_count


def test_import_photo_exports_matching_original_filename() -> None:
    destination = Path("resources/faces")
    photo_library = FakePhotoLibrary(exported_count=1)
    service = ImportPhotoService(photo_library, destination)

    result = service.execute("IMG_1345.HEIC")

    assert result.exported_count == 1
    assert result.destination == destination
    assert photo_library.calls == [("IMG_1345.HEIC", destination)]


def test_import_photo_rejects_empty_original_filename() -> None:
    service = ImportPhotoService(FakePhotoLibrary(exported_count=1), Path("resources/faces"))

    with pytest.raises(ValidationError, match="Original filename must not be empty"):
        service.execute("   ")


def test_import_photo_reports_when_no_photo_matches() -> None:
    service = ImportPhotoService(FakePhotoLibrary(exported_count=0), Path("resources/faces"))

    with pytest.raises(PhotoNotFoundError, match="No photo found with original filename"):
        service.execute("IMG_1345.HEIC")


def test_resize_photo_to_jpeg_scales_to_default_max_side_and_quality(tmp_path: Path) -> None:
    source = tmp_path / "IMG_1345.png"
    image = Image.new("RGB", (2500, 1500), color="red")
    image.save(source)

    result = resize_photo_to_jpeg(source, max_edge=1600, quality=85)

    assert result == source.with_suffix(".jpg")
    assert result.exists()
    with Image.open(result) as converted:
        assert converted.format == "JPEG"
        assert max(converted.size) <= 1600
        assert min(converted.size) <= 1600
        assert converted.mode == "RGB"
    assert not source.exists()


def test_osxphotos_photo_library_counts_match_even_when_export_uses_incremented_filename(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class FakePhoto:
        original_filename = "IMG_1345.HEIC"

    class FakePhotoExporter:
        def __init__(self, photo: FakePhoto) -> None:
            self.photo = photo

        def export(self, destination: Path, *, filename: str, options: object) -> object:
            target = destination / "IMG_1345 (3).jpeg"
            target.write_bytes(b"123")
            return object()

    class FakePhotosDB:
        def photos(self) -> list[FakePhoto]:
            return [FakePhoto()]

    class FakeExportOptions:
        def __init__(self, **kwargs: object) -> None:
            self.__dict__.update(kwargs)

    fake_osxphotos = type(
        "FakeOsxphotos",
        (),
        {
            "ExportOptions": staticmethod(FakeExportOptions),
            "PhotoExporter": staticmethod(FakePhotoExporter),
            "PhotosDB": staticmethod(FakePhotosDB),
        },
    )

    monkeypatch.setattr("style.photos.osxphotos.osxphotos", fake_osxphotos())

    resized: dict[Path, None] = {}

    def fake_resize_photo_to_jpeg(path: Path, **_: object) -> Path:
        resized[path] = None
        return path

    monkeypatch.setattr("style.photos.osxphotos.resize_photo_to_jpeg", fake_resize_photo_to_jpeg)

    result = OsxPhotosPhotoLibrary().export_by_original_filename("IMG_1345.HEIC", tmp_path)

    assert result == 1
    assert len(resized) == 1
