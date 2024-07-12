import os
import shutil
from io import BytesIO
from zipfile import ZipFile

import pytest


async def test_download_of_nested_dirs_and_files(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    nested_file_path = dir_path / "nested.txt"
    nested_file_path.touch()

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 3
    assert "file.txt" in namelist
    assert "dir/" in namelist
    assert "dir/nested.txt" in namelist

    assert len(archive.filelist) == 3
    assert archive.getinfo("dir/").is_dir()
    assert not archive.getinfo("file.txt").is_dir()
    assert not archive.getinfo("dir/nested.txt").is_dir()


async def test_download_of_single_dir(tmp_path, cli):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert "dir/" in namelist

    assert len(archive.filelist) == 1
    assert archive.getinfo("dir/").is_dir()


async def test_download_of_single_file(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert "file.txt" in namelist

    assert len(archive.filelist) == 1
    assert not archive.getinfo("file.txt").is_dir()


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Requires unzip")
async def test_download_of_a_file_symlink(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.write_text("test")

    link_path = tmp_path / "file-link"
    link_path.symlink_to(file_path)

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 2
    assert "file.txt" in namelist
    assert "file-link" in namelist

    archive_path = tmp_path / "archive.zip"
    archive_path.write_bytes(data)

    # Neither zipfile.TarFile.extractall nor shutil.unpack_archive extract symlinks
    os.system(f"unzip -o {archive_path} -d {tmp_path / 'extracted'}")

    extracted_file_path = tmp_path / "extracted" / "file.txt"
    extracted_link_path = tmp_path / "extracted" / "file-link"
    assert extracted_file_path.is_file()
    assert extracted_link_path.is_symlink()
    assert extracted_link_path.resolve() == extracted_file_path.resolve()


@pytest.mark.skipif(shutil.which("unzip") is None, reason="Requires unzip")
@pytest.mark.xfail(reason="Directory symlinks don't appear to be supported upstream")
async def test_download_of_a_directory_symlink(tmp_path, cli):
    dir_path = tmp_path / "some-dir"
    dir_path.mkdir()

    link_path = tmp_path / "dir-link"
    link_path.symlink_to(dir_path, target_is_directory=True)

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 2
    assert "some-dir/" in namelist
    assert "dir-link/" in namelist

    archive_path = tmp_path / "archive.zip"
    archive_path.write_bytes(data)

    # Neither zipfile.TarFile.extractall nor shutil.unpack_archive extract symlinks
    os.system(f"unzip -o {archive_path} -d {tmp_path / 'extracted'}")

    extracted_dir_path = tmp_path / "extracted" / "some-dir"
    extracted_link_path = tmp_path / "extracted" / "dir-link"
    assert extracted_dir_path.is_dir()
    assert extracted_link_path.is_symlink()
    assert extracted_link_path.resolve() == extracted_dir_path.resolve()


async def test_directory_symlinks_are_not_included(tmp_path, cli):
    dir_path = tmp_path / "some-dir"
    dir_path.mkdir()

    link_path = tmp_path / "dir-link"
    link_path.symlink_to(dir_path, target_is_directory=True)

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    assert len(archive.filelist) == 1
    assert archive.getinfo("some-dir/").is_dir()


async def test_empty_directory_results_in_empty_archive(tmp_path, cli):
    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 0


async def test_nonexistent_path_results_in_empty_archive(tmp_path, cli):
    nonexisting_path = tmp_path / "nonexistent"

    response = await cli.get("/default/", params={"path": str(nonexisting_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 0


async def test_member_paths_are_relative(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert str(file_path.absolute()) not in namelist
    assert str(file_path.relative_to(tmp_path)) in namelist


async def test_file_contents_are_preserved(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.write_text("test")

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    with archive.open("file.txt") as file:
        assert file.read() == b"test"


async def test_default_status_code(tmp_path, cli):
    response = await cli.get("/default/", params={"path": str(tmp_path)})
    assert response.status == 200


async def test_custom_chunk_size(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.write_text("a" * 1024)

    response = await cli.get("/custom-chunk-size/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert archive.getinfo("file.txt").file_size == 1024


async def test_custom_status_code(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    response = await cli.get("/custom-status/", params={"path": str(tmp_path)})
    assert response.status == 418

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert "file.txt" in namelist


async def test_custom_reason(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    response = await cli.get("/custom-reason/", params={"path": str(tmp_path)})
    assert response.reason == "OKAY"

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert "file.txt" in namelist


async def test_custom_headers(tmp_path, cli):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    response = await cli.get("/custom-headers/", params={"path": str(tmp_path)})
    assert response.headers["X-TEST"] == "TEST"

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert "file.txt" in namelist
