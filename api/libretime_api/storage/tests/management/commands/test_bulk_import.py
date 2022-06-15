# pylint: disable=protected-access

from pathlib import Path
from shutil import copy
from typing import Tuple
from unittest.mock import MagicMock

import pytest
from model_bakery import baker
from requests_mock import Mocker

from ....._fixtures import AUDIO_FILENAME, fixture_path
from ....management.commands.bulk_import import Importer

FAKE_URL = "https://somehost.com"


@pytest.fixture(name="import_paths")
def _import_paths(tmp_path: Path):
    sub_dir = tmp_path / "dir1/dir2"
    sub_dir.mkdir(parents=True)

    test_file = sub_dir / AUDIO_FILENAME
    copy(fixture_path / AUDIO_FILENAME, test_file)

    return (tmp_path, test_file)


@pytest.fixture(name="track_type")
def _track_type():
    return baker.make(
        "storage.TrackType",
        code="MUS",
        type_name="Music",
        description="Description",
    )


@pytest.fixture(name="importer")
def _importer(requests_mock: Mocker):
    requests_mock.post(f"{FAKE_URL}/rest/media", status_code=200)

    obj = Importer(FAKE_URL, "auth")
    obj._handle_file = MagicMock(wraps=obj._handle_file)
    obj._upload_file = MagicMock(wraps=obj._upload_file)
    obj._delete_file = MagicMock(wraps=obj._delete_file)

    yield obj


def test_importer(
    db,
    import_paths: Tuple[Path, Path],
    importer: Importer,
    track_type,
):
    importer.import_dir(import_paths[0], track_type.code, [".mp3"])

    importer._handle_file.assert_called_with(import_paths[1], track_type.code)
    importer._upload_file.assert_called_with(import_paths[1], track_type.code)
    importer._delete_file.assert_not_called()


def test_importer_and_delete(
    db,
    import_paths: Tuple[Path, Path],
    importer: Importer,
    track_type,
):
    importer.delete_after_upload = True
    importer.import_dir(import_paths[0], track_type.code, [".mp3"])

    importer._handle_file.assert_called_with(import_paths[1], track_type.code)
    importer._upload_file.assert_called_with(import_paths[1], track_type.code)
    importer._delete_file.assert_called_with(import_paths[1])


def test_importer_existing_file(
    db,
    import_paths: Tuple[Path, Path],
    importer: Importer,
    track_type,
):
    baker.make("storage.File", md5="46305a7cf42ee53976c88d337e47e940")

    importer.import_dir(import_paths[0], track_type.code, [".mp3"])

    importer._handle_file.assert_called_with(import_paths[1], track_type.code)
    importer._upload_file.assert_not_called()
    importer._delete_file.assert_not_called()


def test_importer_existing_file_and_delete(
    db,
    import_paths: Tuple[Path, Path],
    importer: Importer,
    track_type,
):
    baker.make("storage.File", md5="46305a7cf42ee53976c88d337e47e940")

    importer.delete_if_exists = True
    importer.import_dir(import_paths[0], track_type.code, [".mp3"])

    importer._handle_file.assert_called_with(import_paths[1], track_type.code)
    importer._upload_file.assert_not_called()
    importer._delete_file.assert_called_with(import_paths[1])


def test_importer_missing_track_type(
    db,
    import_paths: Tuple[Path, Path],
    importer: Importer,
):
    with pytest.raises(
        ValueError,
        match="provided track type MISSING does not exist",
    ):
        importer.import_dir(import_paths[0], "MISSING", [".mp3"])
