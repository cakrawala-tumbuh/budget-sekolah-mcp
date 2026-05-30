"""
Tool MCP untuk membaca daftar kategori (read-only).

Menyediakan tool untuk mengambil daftar kategori biaya, pendapatan,
dan investasi yang di-seed otomatis oleh backend saat startup.
Data ini dibutuhkan untuk mengetahui ``id`` kategori sebelum membuat
entri anggaran.

Tools yang tersedia:
  list_expense_categories    — Daftar kategori biaya (akun 5110–5590)
  list_income_categories     — Daftar kategori pendapatan (akun 4110–4620)
  list_investment_categories — Daftar kategori investasi (akun 1330.01–1330.08)

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool kategori ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_expense_categories() -> dict:
        """Ambil daftar semua kategori biaya yang tersedia di sistem.

        Kategori biaya mencakup akun operasional (5110–5250) dan
        non-operasional (5500–5590). Gunakan ``id`` dari hasil ini
        saat membuat atau mengupdate entri anggaran biaya.

        Returns:
            Dict dengan kunci ``items`` berisi list kategori biaya,
            masing-masing memiliki ``id``, ``account_code``, ``name``,
            dan ``category_type`` (OPERATIONAL atau NON_OPERATIONAL).
            Atau kunci ``error`` jika request gagal.

        Example:
            >>> result = await list_expense_categories()
            >>> result["items"][0]["account_code"]
            '5110.01'
        """
        response = await client.get("/expense-categories")
        if response.status_code == 200:
            return {"items": response.json()}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def list_income_categories() -> dict:
        """Ambil daftar semua kategori pendapatan yang tersedia di sistem.

        Kategori pendapatan mencakup akun 4110–4620. Gunakan ``id`` dari
        hasil ini saat membuat atau mengupdate entri pendapatan manual.
        Perhatikan: tidak semua akun pendapatan perlu diisi manual —
        beberapa dihitung otomatis dari simulasi (UP, US, BOS).

        Returns:
            Dict dengan kunci ``items`` berisi list kategori pendapatan,
            masing-masing memiliki ``id``, ``account_code``, dan ``name``.
            Atau kunci ``error`` jika request gagal.

        Example:
            >>> result = await list_income_categories()
            >>> result["items"][0]["account_code"]
            '4110.01'
        """
        response = await client.get("/income-categories")
        if response.status_code == 200:
            return {"items": response.json()}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def list_investment_categories() -> dict:
        """Ambil daftar semua kategori investasi aset tetap yang tersedia.

        Kategori investasi mencakup akun 1330.01–1330.08 (Kendaraan,
        Kantor, Meubelair, dst.). Gunakan ``id`` dari hasil ini saat
        mencatat investasi aset baru.

        Returns:
            Dict dengan kunci ``items`` berisi list kategori investasi,
            masing-masing memiliki ``id``, ``account_code``, dan ``name``.
            Atau kunci ``error`` jika request gagal.

        Example:
            >>> result = await list_investment_categories()
            >>> result["items"][6]["account_code"]
            '1330.07'
        """
        response = await client.get("/investment-categories")
        if response.status_code == 200:
            return {"items": response.json()}
        return {"error": response.text, "status_code": response.status_code}
