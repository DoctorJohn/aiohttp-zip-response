from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from aiohttp import web
from aiohttp.typedefs import LooseHeaders, PathLike
from stream_zip import ZIP_32, async_stream_zip  # type: ignore


class ZipResponse(web.Response):
    def __init__(
        self,
        path: PathLike,
        chunk_size: int = 256 * 1024,
        status: int = 200,
        reason: Optional[str] = None,
        headers: Optional[LooseHeaders] = None,
    ) -> None:
        self._path = Path(path)
        self._chunk_size = chunk_size
        return super().__init__(
            body=async_stream_zip(self.yield_members()),
            status=status,
            reason=reason,
            headers=headers,
        )

    async def yield_members(self):
        for sub_path in self._path.glob("**/*"):
            lstat = sub_path.lstat()
            yield (
                str(sub_path.relative_to(self._path)),
                datetime.fromtimestamp(lstat.st_mtime),
                lstat.st_mode,
                ZIP_32,
                self.yield_contents(sub_path),
            )

    async def yield_contents(self, file_path: Path) -> AsyncGenerator[bytes, None]:
        if file_path.is_dir():
            return

        with file_path.open("rb") as file:
            while True:
                chunk = file.read(self._chunk_size)
                if not chunk:
                    break
                yield chunk
