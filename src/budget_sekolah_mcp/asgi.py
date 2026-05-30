"""
ASGI entrypoint untuk deployment HTTP/SSE menggunakan uvicorn.

Strategi autentikasi (dipilih otomatis berdasarkan konfigurasi):

  1. **OAuth 2.0** (diutamakan): Aktif jika ``MCP_BASE_URL`` dikonfigurasi.
     FastMCP menangani OAuth natively — mendukung Dynamic Client Registration
     sehingga Claude.ai dan MCP client lain dapat terhubung langsung.

  2. **API Key** (legacy): Aktif jika ``MCP_BASE_URL`` tidak dikonfigurasi
     tetapi ``MCP_API_KEY`` dikonfigurasi. Setiap request wajib menyertakan
     header ``X-API-Key`` atau ``Authorization: Bearer``.

  3. **Tanpa auth**: Aktif jika keduanya tidak dikonfigurasi.
     Cocok untuk stdio transport atau jaringan tertutup.

Cara menjalankan:
  uvicorn budget_sekolah_mcp.asgi:app --host 0.0.0.0 --port 9170

Catatan keamanan:
  - Pastikan salah satu dari MCP_BASE_URL atau MCP_API_KEY diisi untuk
    deployment cloud/production.
  - Transport stdio (``__main__.py``) tidak menggunakan modul ini.
"""

import logging

from .config import settings
from .middleware import ApiKeyMiddleware
from .server import mcp

logger = logging.getLogger(__name__)

# Buat ASGI app dari FastMCP dengan transport SSE.
_base_app = mcp.http_app(transport="sse")

if settings.mcp_base_url:
    # OAuth aktif via FastMCP native — tidak perlu wrapper tambahan.
    logger.info("Mode autentikasi: OAuth 2.0 (MCP_BASE_URL dikonfigurasi).")
    app = _base_app
elif settings.mcp_api_key:
    # Legacy: gunakan ApiKeyMiddleware untuk static Bearer token.
    logger.info("Mode autentikasi: API Key legacy (MCP_API_KEY dikonfigurasi).")
    app = ApiKeyMiddleware(_base_app, api_key=settings.mcp_api_key)
else:
    logger.warning(
        "MCP_BASE_URL dan MCP_API_KEY tidak dikonfigurasi — server berjalan "
        "TANPA autentikasi. Tambahkan MCP_BASE_URL untuk deployment cloud."
    )
    app = _base_app
