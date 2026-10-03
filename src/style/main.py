from pathlib import Path

from style.cli import create_app
from style.photos.import_photo import ImportPhotoService
from style.photos.osxphotos import OsxPhotosPhotoLibrary

app = create_app(ImportPhotoService(OsxPhotosPhotoLibrary(), Path("resources/faces")))
