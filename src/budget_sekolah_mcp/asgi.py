"""
ASGI entrypoint untuk deployment HTTP/SSE menggunakan uvicorn.

Menggunakan ``mcp.http_app(transport='sse')`` dari FastMCP dan membungkusnya
dengan ``ApiKeyMiddleware`` jika ``MCP_API_KEY`` dikonfigurasi.

Cara menjalankan:
  uvicorn budget_sekolah_mcp.asgi:app --host 0.0.0.0 --port 9170

Catatan keamanan:
  - Jika ``MCP_API_KEY`` tidak dikonfigurasi, server berjalan TANPA autentikasi.
    Pastikan variabel ini diisi di lingkungan cloud/production.
  - Transport stdio (``__main__.py``) tidak menggunakan modul ini — stdio
    diamankan oleh isolasi proses (AI client yang spawn prosesnya).
"""

import logging

from .config import settings
from .middleware import ApiKeyMiddleware
from .server import mcp

logger = logging.getLogger(__name__)

# Buat ASGI app dari FastMCP dengan transport SSE.
# StarletteWithLifespan sudah menyertakan lifespan dari mcp (login + cleanup).
_base_app = mcp.http_app(transport="sse")

if settings.mcp_api_key:
    logger.info("API key authentication AKTIF untuk endpoint SSE.")
    app = ApiKeyMiddleware(_base_app, api_key=settings.mcp_api_key)
else:
    logger.warning(
        "MCP_API_KEY tidak dikonfigurasi — server berjalan TANPA autentikasi. "
        "Tambahkan MCP_API_KEY ke environment untuk deployment cloud."
    )
    app = _base_app
