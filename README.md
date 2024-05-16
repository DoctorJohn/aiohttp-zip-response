# AIOHTTP ZIP Response

A AIOHTTP response class streaming a directory as ZIP archive.

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
