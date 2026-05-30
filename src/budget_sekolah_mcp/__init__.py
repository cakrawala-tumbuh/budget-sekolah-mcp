"""
budget-sekolah-mcp — MCP server untuk budget-backend-ypii.

Paket ini menyediakan server MCP yang memungkinkan AI agent berinteraksi
dengan API simulasi anggaran sekolah YPII melalui antarmuka MCP standar.

Ekspor utama:
  mcp    — instance FastMCP yang dapat di-mount atau dijalankan langsung
  client — instance BudgetApiClient (dibuat saat import)
"""

from .server import mcp

__all__ = ["mcp"]
