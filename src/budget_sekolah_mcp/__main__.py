"""
Entry point untuk menjalankan MCP server via `python -m budget_sekolah_mcp`.

Menjalankan FastMCP dengan transport stdio (default untuk AI client seperti
Claude Desktop dan VS Code Copilot).
"""

from .server import mcp


def main() -> None:
    """Jalankan MCP server dengan transport stdio.

    Digunakan sebagai entry point untuk integrasi dengan AI client yang
    berkomunikasi melalui stdin/stdout (contoh: Claude Desktop).
    """
    mcp.run()


if __name__ == "__main__":
    main()
