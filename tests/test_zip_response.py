from io import BytesIO
from zipfile import ZipFile


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
    assert "dir" in namelist
    assert "dir/nested.txt" in namelist


async def test_download_of_single_dir(tmp_path, cli):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    response = await cli.get("/default/", params={"path": str(tmp_path)})
    response.raise_for_status()

    data = await response.read()
    archive = ZipFile(BytesIO(data))

    namelist = archive.namelist()
    assert len(namelist) == 1
    assert "dir" in namelist


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
    assert str(file_path.absolute) not in namelist
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
    assert archive.getinfo(namelist[0]).file_size == 1024


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
