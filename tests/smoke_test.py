import asyncio
import tempfile
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from aiohttp_zip_response import ZipResponse

FILE_CONTENT = b"Hello, World!\n" * 1000
NESTED_FILE_CONTENT = b"nested"


async def stream_zip(base_path: Path) -> bytes:
    async def handle_zip(request: web.Request) -> web.StreamResponse:
        # A small chunk size makes sure files are streamed in multiple chunks
        return ZipResponse(base_path, chunk_size=1024)

    app = web.Application()
    app.router.add_get("/zip", handle_zip)

    async with TestClient(TestServer(app)) as client:
        response = await client.get("/zip")
        assert response.status == 200, response.status
        return await response.read()


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        (base_path / "file.txt").write_bytes(FILE_CONTENT)
        (base_path / "dir").mkdir()
        (base_path / "dir" / "nested.txt").write_bytes(NESTED_FILE_CONTENT)

        data = await stream_zip(base_path)

    with ZipFile(BytesIO(data)) as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == ["dir/", "dir/nested.txt", "file.txt"]
        assert archive.read("file.txt") == FILE_CONTENT
        assert archive.read("dir/nested.txt") == NESTED_FILE_CONTENT

    print(f"Smoke test passed: streamed {len(data)} bytes ZIP archive")


if __name__ == "__main__":
    asyncio.run(main())
