import pytest
from aiohttp import web

from aiohttp_zip_response import ZipResponse


async def default_handler(request: web.Request) -> web.StreamResponse:
    return ZipResponse(
        request.query["path"],
    )


async def custom_chunk_size_handler(request: web.Request) -> web.StreamResponse:
    return ZipResponse(
        request.query["path"],
        chunk_size=256 * 1024,
    )


async def custom_status_handler(request: web.Request) -> web.StreamResponse:
    return ZipResponse(
        request.query["path"],
        status=418,
    )


async def custom_reason_handler(request: web.Request) -> web.StreamResponse:
    return ZipResponse(
        request.query["path"],
        reason="OKAY",
    )


async def custom_headers_handler(request: web.Request) -> web.StreamResponse:
    return ZipResponse(
        request.query["path"],
        headers={"X-TEST": "TEST"},
    )


@pytest.fixture
async def cli(aiohttp_client):
    app = web.Application()
    app.router.add_get("/default/", default_handler)
    app.router.add_get("/custom-chunk-size/", custom_chunk_size_handler)
    app.router.add_get("/custom-status/", custom_status_handler)
    app.router.add_get("/custom-reason/", custom_reason_handler)
    app.router.add_get("/custom-headers/", custom_headers_handler)
    return await aiohttp_client(app)
