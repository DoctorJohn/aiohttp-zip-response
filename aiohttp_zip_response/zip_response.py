from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from aiohttp import web
from aiohttp.typedefs import LooseHeaders, PathLike
from stream_zip import ZIP_32, AsyncMemberFile, async_stream_zip


class ZipResponse(web.StreamResponse):
    def __init__(
        self,
        base_path: PathLike,
        chunk_size: int = 256 * 1024,
        status: int = 200,
        reason: Optional[str] = None,
        headers: Optional[LooseHeaders] = None,
    ) -> None:
        self._base_path = Path(base_path)
        self._chunk_size = chunk_size
        return super().__init__(
            status=status,
            reason=reason,
            headers=headers,
        )

    async def prepare(self, request: web.BaseRequest) -> None:
        await super().prepare(request)

        async for chunk in async_stream_zip(self.yield_member_files()):
            await self.write(chunk)

        await self.write_eof()

    async def yield_member_paths(self) -> AsyncGenerator[Path, None]:
        for member_path in self._base_path.glob("**/*"):
            yield member_path

    async def yield_member_files(self) -> AsyncGenerator[AsyncMemberFile, None]:
        async for member_path in self.yield_member_paths():
            lstat = member_path.lstat()
            relative_member_path = member_path.relative_to(self._base_path)

            if member_path.is_symlink():
                if member_path.is_file():
                    yield (
                        str(relative_member_path),
                        datetime.fromtimestamp(lstat.st_mtime),
                        lstat.st_mode,
                        ZIP_32,
                        self.yield_symlink_member_chunks(member_path),
                    )

            elif member_path.is_file():
                yield (
                    str(relative_member_path),
                    datetime.fromtimestamp(lstat.st_mtime),
                    lstat.st_mode,
                    ZIP_32,
                    self.yield_file_member_chunks(member_path),
                )

            elif member_path.is_dir():
                yield (
                    f"{relative_member_path}/",
                    datetime.fromtimestamp(lstat.st_mtime),
                    lstat.st_mode,
                    ZIP_32,
                    self.yield_dir_member_chunks(member_path),
                )

    async def yield_symlink_member_chunks(
        self, path: Path
    ) -> AsyncGenerator[bytes, None]:
        yield str(path.resolve().relative_to(self._base_path)).encode()
        return

    async def yield_file_member_chunks(self, path: Path) -> AsyncGenerator[bytes, None]:
        with path.open("rb") as file:
            while True:
                chunk = file.read(self._chunk_size)
                if not chunk:
                    break
                yield chunk

    async def yield_dir_member_chunks(self, path: Path) -> AsyncGenerator[bytes, None]:
        return
        yield b""  # pragma: no cover
