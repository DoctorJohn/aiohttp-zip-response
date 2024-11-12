# AIOHTTP ZIP Response

[![Versions][versions-image]][versions-url]
[![PyPI][pypi-image]][pypi-url]
[![Codecov][codecov-image]][codecov-url]
[![License][license-image]][license-url]

[versions-image]: https://img.shields.io/pypi/pyversions/aiohttp-zip-response
[versions-url]: https://github.com/DoctorJohn/aiohttp-zip-response/blob/main/pyproject.toml
[pypi-image]: https://img.shields.io/pypi/v/aiohttp-zip-response
[pypi-url]: https://pypi.org/project/aiohttp-zip-response/
[codecov-image]: https://codecov.io/gh/DoctorJohn/aiohttp-zip-response/branch/main/graph/badge.svg
[codecov-url]: https://codecov.io/gh/DoctorJohn/aiohttp-zip-response
[license-image]: https://img.shields.io/pypi/l/aiohttp-zip-response
[license-url]: https://github.com/DoctorJohn/aiohttp-zip-response/blob/main/LICENSE

A AIOHTTP response class streaming the contents of a directory as a ZIP archive.
Thanks to [stream-zip](https://github.com/uktrade/stream-zip/), this works **without storing the entire ZIP in memory or disk**.

Generally, this package is meant to complement the existing `aiohttp.web.FileResponse` class which can be used to stream the contents of a single file.

## Installation

```bash
pip install aiohttp-zip-response
```

## Usage

```python
from aiohttp import web
from aiohttp_zip_response import ZipResponse


async def handle_zip(request):
    return ZipResponse('path/to/directory')


app = web.Application()
app.router.add_get('/zip', handle_zip)
web.run_app(app)
```

## Caveats

- The `Content-Length` header is not set because the size of the ZIP archive is not known in advance. This means clients such as browsers cannot display a download progress bar.
- This package currently doesn't support streaming of symbolic links to directories.
