from pathlib import Path

from typer.testing import CliRunner

from style.cli import create_app
from style.photos.import_photo import ImportPhotoResult
from style.tryon.generator import TryOnGenerationError
from style.tryon.try_on import TryOnResult

runner = CliRunner()


class UnusedImportPhotoService:
    def execute(self, original_filename: str) -> ImportPhotoResult:
        raise AssertionError(original_filename)


class UnusedTryOnService:
    def execute(self, face: Path, frame: Path) -> TryOnResult:
        raise AssertionError((face, frame))


def test_import_photo_exports_matching_original_filename() -> None:
    class FakeImportPhotoService:
        def execute(self, original_filename: str) -> ImportPhotoResult:
            assert original_filename == "IMG_1345.HEIC"
            return ImportPhotoResult(exported_count=1, destination=Path("resources/faces"))

    result = runner.invoke(
        create_app(FakeImportPhotoService(), UnusedTryOnService()),
        ["import-photo", "IMG_1345.HEIC"],
    )

    assert result.exit_code == 0
    assert result.output == "Exported 1 photo(s) to resources/faces\n"


def test_try_on_saves_generated_image() -> None:
    class FakeTryOnService:
        def execute(self, face: Path, frame: Path) -> TryOnResult:
            assert (face, frame) == (Path("face.jpeg"), Path("frame.jpg"))
            return TryOnResult(output=Path("resources/try-ons/face__frame.png"))

    result = runner.invoke(
        create_app(UnusedImportPhotoService(), FakeTryOnService()),
        ["try-on", "face.jpeg", "frame.jpg"],
    )

    assert result.exit_code == 0
    assert result.output == "Saved try-on to resources/try-ons/face__frame.png\n"


def test_try_on_reports_generation_failure() -> None:
    class FailingTryOnService:
        def execute(self, face: Path, frame: Path) -> TryOnResult:
            raise TryOnGenerationError("OpenAI image edit failed (401): bad key")

    result = runner.invoke(
        create_app(UnusedImportPhotoService(), FailingTryOnService()),
        ["try-on", "face.jpeg", "frame.jpg"],
    )

    assert result.exit_code == 1
    assert "bad key" in result.output
