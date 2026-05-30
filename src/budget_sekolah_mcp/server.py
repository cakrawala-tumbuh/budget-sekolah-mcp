"""
Entry point FastMCP — instansiasi server dan registrasi semua tool.

Server menggunakan pola lifespan untuk:
  1. Login ke backend API saat startup
  2. Menutup koneksi HTTP saat shutdown

Semua tool diregistrasikan dengan memanggil fungsi register_*() dari
masing-masing modul tools/ setelah instance mcp dan client dibuat.

Cara menjalankan:
  # stdio (untuk AI client)
  python -m budget_sekolah_mcp

  # SSE (untuk testing via browser/curl, port 9170)
  fastmcp run src/budget_sekolah_mcp/server.py --transport sse --port 9170
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastmcp import FastMCP

from .client import BudgetApiClient
from .config import settings

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


mcp = FastMCP(name=settings.mcp_server_name, lifespan=lifespan)

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
