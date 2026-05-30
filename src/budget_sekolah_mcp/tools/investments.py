"""
Tool MCP untuk investasi aset tetap baru.

Menyediakan tool CRUD untuk Investment — pembelian aset tetap baru yang
depresiasi proporsionalnya dihitung otomatis berdasarkan purchase_price,
useful_life, dan start_month.

Tools yang tersedia:
  list_investments    — Daftar investasi aset baru untuk satu organisasi
  create_investment   — Catat satu aset baru
  update_investment   — Update data satu aset
  delete_investment   — Hapus satu aset

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool investasi ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_investments(org_id: int) -> dict:
        """Ambil daftar investasi aset tetap baru untuk satu organisasi.

        Args:
            org_id: ID numerik organisasi.

        Returns:
            Dict dengan kunci ``items`` berisi list investasi, masing-masing
            termasuk ``dep_per_year`` (depresiasi per tahun penuh) dan
            ``dep_current_year`` (depresiasi proporsional tahun berjalan).
            Atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/investments")
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def create_investment(
        org_id: int,
        investment_category_id: int,
        asset_name: str,
        purchase_price: float,
        useful_life: int,
        start_month: int,
        asset_code: str | None = None,
    ) -> dict:
        """Catat satu aset tetap baru untuk satu organisasi.

        Depresiasi proporsional tahun berjalan dihitung otomatis oleh backend:
        ``dep_current_year = (purchase_price / useful_life) × (13 - start_month) / 12``

        Args:
            org_id: ID numerik organisasi.
            investment_category_id: ID kategori investasi (1330.01–1330.08).
            asset_name: Nama spesifik aset (contoh: "Laptop Acer Aspire 5 (30 unit)").
            purchase_price: Harga total perolehan aset dalam Rupiah.
            useful_life: Umur ekonomis aset dalam tahun.
            start_month: Bulan pertama aset mulai dipakai (1–12).
            asset_code: Kode inventaris aset (opsional).

        Returns:
            Dict data investasi yang dibuat, atau kunci ``error`` jika gagal.

        Example:
            >>> result = await create_investment(
            ...     org_id=3, investment_category_id=7,
            ...     asset_name="Laptop (30 unit)", purchase_price=360000000,
            ...     useful_life=4, start_month=7
            ... )
            >>> result["dep_current_year"]
            45000000.0
        """
        payload: dict = {
            "investment_category_id": investment_category_id,
            "asset_name": asset_name,
            "purchase_price": purchase_price,
            "useful_life": useful_life,
            "start_month": start_month,
        }
        if asset_code is not None:
            payload["asset_code"] = asset_code

        response = await client.post(f"/organizations/{org_id}/investments", json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_investment(
        org_id: int,
        investment_id: int,
        investment_category_id: int | None = None,
        asset_code: str | None = None,
        asset_name: str | None = None,
        purchase_price: float | None = None,
        useful_life: int | None = None,
        start_month: int | None = None,
    ) -> dict:
        """Update data satu aset tetap baru.

        Args:
            org_id: ID numerik organisasi.
            investment_id: ID numerik investasi yang akan diupdate.
            investment_category_id: ID kategori baru (opsional).
            asset_code: Kode inventaris baru (opsional).
            asset_name: Nama aset baru (opsional).
            purchase_price: Harga beli baru dalam Rupiah (opsional).
            useful_life: Umur ekonomis baru dalam tahun (opsional).
            start_month: Bulan mulai baru (opsional).

        Returns:
            Dict data investasi setelah diupdate, atau kunci ``error`` jika gagal.
        """
        payload: dict = {}
        if investment_category_id is not None:
            payload["investment_category_id"] = investment_category_id
        if asset_code is not None:
            payload["asset_code"] = asset_code
        if asset_name is not None:
            payload["asset_name"] = asset_name
        if purchase_price is not None:
            payload["purchase_price"] = purchase_price
        if useful_life is not None:
            payload["useful_life"] = useful_life
        if start_month is not None:
            payload["start_month"] = start_month

        response = await client.put(
            f"/organizations/{org_id}/investments/{investment_id}",
            json=payload,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Investment atau organization tidak ditemukan"}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_investment(org_id: int, investment_id: int) -> dict:
        """Hapus satu aset tetap baru.

        Args:
            org_id: ID numerik organisasi.
            investment_id: ID numerik investasi yang akan dihapus.

        Returns:
            Dict ``{"success": True}`` jika berhasil, atau kunci ``error`` jika gagal.
        """
        response = await client.delete(f"/organizations/{org_id}/investments/{investment_id}")
        if response.status_code == 204:
            return {"success": True}
        if response.status_code == 404:
            return {"error": "Investment tidak ditemukan", "investment_id": investment_id}
        return {"error": response.text, "status_code": response.status_code}
