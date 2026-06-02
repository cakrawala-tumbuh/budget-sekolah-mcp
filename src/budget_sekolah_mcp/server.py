"""
Entry point FastMCP — instansiasi server dan registrasi semua tool.

Server menggunakan pola lifespan untuk:
  1. Login ke backend API saat startup
  2. Menutup koneksi HTTP saat shutdown

Autentikasi (dipilih otomatis berdasarkan konfigurasi):
  - Authentik OAuth (Claude.ai): Aktif jika AUTHENTIK_BASE_URL, AUTHENTIK_APP_SLUG,
    AUTHENTIK_CLIENT_ID, AUTHENTIK_CLIENT_SECRET, dan MCP_BASE_URL dikonfigurasi.
    Pengguna login via Authentik; hanya username yang tercantum di
    AUTHENTIK_ALLOWED_USERNAMES yang diizinkan (kosong = semua user).
  - API Key (VS Code / tools lain): Aktif jika MCP_API_KEY dikonfigurasi.
    Request wajib menyertakan header 'Authorization: Bearer <key>'.
  - Keduanya bisa aktif bersamaan via MultiAuth.
  - Tanpa konfigurasi: tidak ada auth (hanya untuk stdio atau jaringan lokal).

Semua tool diregistrasikan dengan memanggil fungsi register_*() dari
masing-masing modul tools/ setelah instance mcp dan client dibuat.

Cara menjalankan:
  # stdio (untuk AI client lokal)
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


# ── Auth provider (dipilih otomatis) ─────────────────────────────────────────
_auth = None
_authentik_oauth_aktif = (
    settings.authentik_base_url
    and settings.authentik_app_slug
    and settings.authentik_client_id
    and settings.authentik_client_secret
    and settings.mcp_base_url
)

if _authentik_oauth_aktif:
    from fastmcp.server.auth import MultiAuth

    from .auth_provider import AuthentikProvider, BearerApiKeyVerifier

    logger.info(
        "OAuth Authentik AKTIF — base_url: %s | slug: %s | allowed: %s",
        settings.authentik_base_url,
        settings.authentik_app_slug,
        settings.authentik_allowed_usernames or "(semua diizinkan)",
    )
    _authentik_provider = AuthentikProvider(
        authentik_base_url=settings.authentik_base_url,
        application_slug=settings.authentik_app_slug,
        client_id=settings.authentik_client_id,
        client_secret=settings.authentik_client_secret,
        base_url=settings.mcp_base_url,
        allowed_usernames=settings.authentik_allowed_usernames,
        require_authorization_consent="external",
    )
    if settings.mcp_api_key:
        logger.info("API Key AKTIF (MultiAuth: Authentik OAuth + API Key)")
        _auth = MultiAuth(
            server=_authentik_provider,
            verifiers=[BearerApiKeyVerifier(api_key=settings.mcp_api_key)],
        )
    else:
        _auth = _authentik_provider

elif settings.mcp_api_key:
    from fastmcp.server.auth import MultiAuth

    from .auth_provider import BearerApiKeyVerifier

    logger.info("API Key AKTIF (tanpa OAuth)")
    _auth = MultiAuth(verifiers=[BearerApiKeyVerifier(api_key=settings.mcp_api_key)])

else:
    logger.warning(
        "Tidak ada autentikasi dikonfigurasi — server berjalan terbuka. "
        "Tambahkan AUTHENTIK_* dan MCP_BASE_URL untuk deployment cloud."
    )


mcp = FastMCP(name=settings.mcp_server_name, lifespan=lifespan, auth=_auth)

# ── Registrasi tools ──────────────────────────────────────────────────────────
# Import dilakukan setelah mcp dan _client dibuat untuk menghindari circular import.
from .tools import (  # noqa: E402
    assumptions,
    budget_entries,
    categories,
    contributions,
    depreciation,
    grade_configs,
    income_entries,
    investments,
    organizations,
    parent_expense_allocations,
    simulation,
    subsidies,
)

assumptions.register(mcp, _client)
budget_entries.register(mcp, _client)
categories.register(mcp, _client)
contributions.register(mcp, _client)
depreciation.register(mcp, _client)
grade_configs.register(mcp, _client)
income_entries.register(mcp, _client)
investments.register(mcp, _client)
organizations.register(mcp, _client)
parent_expense_allocations.register(mcp, _client)
simulation.register(mcp, _client)
subsidies.register(mcp, _client)
