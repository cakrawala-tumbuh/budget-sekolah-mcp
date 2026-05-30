"""
Entry point FastMCP — instansiasi server dan registrasi semua tool.

Server menggunakan pola lifespan untuk:
  1. Login ke backend API saat startup
  2. Menutup koneksi HTTP saat shutdown

Autentikasi:
  - Jika MCP_BASE_URL dikonfigurasi, OAuth 2.0 bawaan FastMCP diaktifkan.
    Claude.ai dan MCP client lain dapat terhubung via OAuth Dynamic Client
    Registration (RFC 7591).
  - Jika MCP_BASE_URL tidak dikonfigurasi, tidak ada auth di level server
    (gunakan ApiKeyMiddleware di asgi.py, atau jalankan via stdio).

Semua tool diregistrasikan dengan memanggil fungsi register_*() dari
masing-masing modul tools/ setelah instance mcp dan client dibuat.

Cara menjalankan:
  # stdio (untuk AI client)
  python -m budget_sekolah_mcp

  # SSE (untuk testing via browser/curl, port 9170)
  fastmcp run src/budget_sekolah_mcp/server.py --transport sse --port 9170
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp import FastMCP

from .client import BudgetApiClient
from .config import settings

logger = logging.getLogger(__name__)

# ── Singleton client — digunakan oleh semua tool ─────────────────────────────
_client = BudgetApiClient()


@asynccontextmanager
async def lifespan(_app: FastMCP) -> AsyncGenerator[None, None]:
    """Lifecycle hooks: login saat startup, close client saat shutdown.

    Args:
        _app: Instance FastMCP (tidak digunakan langsung, parameter wajib).

    Yields:
        None — kontrol dikembalikan ke server selama running.
    """
    await _client.startup()
    try:
        yield
    finally:
        await _client.aclose()


# ── OAuth provider (opsional) ─────────────────────────────────────────────────
_auth = None
if settings.mcp_base_url:
    from fastmcp.server.auth.auth import ClientRegistrationOptions, OAuthProvider

    logger.info("OAuth 2.0 AKTIF — base_url: %s", settings.mcp_base_url)
    _auth = OAuthProvider(
        base_url=settings.mcp_base_url,
        client_registration_options=ClientRegistrationOptions(enabled=True),
    )
else:
    logger.info("MCP_BASE_URL tidak dikonfigurasi — OAuth tidak aktif.")


mcp = FastMCP(name=settings.mcp_server_name, lifespan=lifespan, auth=_auth)

# ── Registrasi tools ──────────────────────────────────────────────────────────
# Import dilakukan setelah mcp dan _client dibuat untuk menghindari circular import.
from .tools import (  # noqa: E402
    assumptions,
    budget_entries,
    categories,
    contributions,
    depreciation,
    income_entries,
    investments,
    organizations,
    simulation,
)

assumptions.register(mcp, _client)
budget_entries.register(mcp, _client)
categories.register(mcp, _client)
contributions.register(mcp, _client)
depreciation.register(mcp, _client)
income_entries.register(mcp, _client)
investments.register(mcp, _client)
organizations.register(mcp, _client)
simulation.register(mcp, _client)
