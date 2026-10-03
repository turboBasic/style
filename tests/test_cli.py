from pathlib import Path

from typer.testing import CliRunner

from style.cli import create_app
from style.photos.import_photo import ImportPhotoResult

runner = CliRunner()


def test_import_photo_exports_matching_original_filename() -> None:
    class FakeImportPhotoService:
        def execute(self, original_filename: str) -> ImportPhotoResult:
            assert original_filename == "IMG_1345.HEIC"
            return ImportPhotoResult(exported_count=1, destination=Path("resources/faces"))

    result = runner.invoke(create_app(FakeImportPhotoService()), ["import-photo", "IMG_1345.HEIC"])

    assert result.exit_code == 0
    assert result.output == "Exported 1 photo(s) to resources/faces\n"
