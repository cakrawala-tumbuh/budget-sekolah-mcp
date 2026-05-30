"""
ASGI entrypoint untuk deployment HTTP/SSE menggunakan uvicorn.

Autentikasi ditangani sepenuhnya di dalam objek ``mcp`` (lihat server.py):
  - GitHub OAuth + API Key (MultiAuth): jika GITHUB_CLIENT_ID/SECRET + MCP_BASE_URL diisi
  - API Key saja: jika hanya MCP_API_KEY yang diisi
  - Tanpa auth: jika tidak ada yang dikonfigurasi (stdio / jaringan lokal)

Modul ini hanya membungkus ``mcp`` menjadi ASGI app dengan transport SSE.

Cara menjalankan:
  uvicorn budget_sekolah_mcp.asgi:app --host 0.0.0.0 --port 9170
"""

import logging

from .server import mcp

logger = logging.getLogger(__name__)

# Buat ASGI app dari FastMCP dengan transport SSE.
# Auth sudah dihandle di dalam mcp — tidak perlu wrapper tambahan.
app = mcp.http_app(transport="sse")
logger.info("ASGI app siap (transport=sse, port=9170)")
