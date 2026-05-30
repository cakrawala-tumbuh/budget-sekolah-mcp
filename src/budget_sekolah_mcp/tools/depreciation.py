"""
Tool MCP untuk aset tetap lama yang masih disusutkan.

Menyediakan tool CRUD untuk DepreciationOldAsset — aset yang dibeli sebelum
tahun anggaran berjalan namun masih memiliki sisa masa manfaat.
Depresiasi dihitung dengan metode garis lurus.

Tools yang tersedia:
  list_old_assets    — Daftar aset lama untuk satu organisasi
  create_old_asset   — Catat satu aset lama
  update_old_asset   — Update data satu aset lama
  delete_old_asset   — Hapus satu aset lama

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool depresiasi ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_old_assets(org_id: int) -> dict:
        """Ambil daftar aset tetap lama yang masih disusutkan untuk satu organisasi.

        Args:
            org_id: ID numerik organisasi.

        Returns:
            Dict dengan kunci ``items`` berisi list aset lama, masing-masing
            termasuk ``dep_per_year`` (depresiasi tahunan garis lurus).
            Atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/depreciation")
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def create_old_asset(
        org_id: int,
        asset_name: str,
        acquisition_cost: float,
        useful_life: int,
        acquisition_year: int,
        asset_code: str | None = None,
    ) -> dict:
        """Catat satu aset tetap lama yang masih dalam masa penyusutan.

        Depresiasi garis lurus per tahun dihitung otomatis:
        ``dep_per_year = acquisition_cost / useful_life``

        Args:
            org_id: ID numerik organisasi.
            asset_name: Nama aset (contoh: "Komputer Desktop Lama (10 unit)").
            acquisition_cost: Harga perolehan aset dalam Rupiah.
            useful_life: Umur ekonomis total aset dalam tahun.
            acquisition_year: Tahun pertama aset dibeli (contoh: 2022).
            asset_code: Kode inventaris aset (opsional).

        Returns:
            Dict data aset yang dibuat, atau kunci ``error`` jika gagal.

        Example:
            >>> result = await create_old_asset(
            ...     org_id=3, asset_name="Komputer lama (10 unit)",
            ...     acquisition_cost=50000000, useful_life=5, acquisition_year=2022
            ... )
            >>> result["dep_per_year"]
            10000000.0
        """
        payload: dict = {
            "asset_name": asset_name,
            "acquisition_cost": acquisition_cost,
            "useful_life": useful_life,
            "acquisition_year": acquisition_year,
        }
        if asset_code is not None:
            payload["asset_code"] = asset_code

        response = await client.post(f"/organizations/{org_id}/depreciation", json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_old_asset(
        org_id: int,
        asset_id: int,
        asset_code: str | None = None,
        asset_name: str | None = None,
        acquisition_cost: float | None = None,
        useful_life: int | None = None,
        acquisition_year: int | None = None,
    ) -> dict:
        """Update data satu aset tetap lama.

        Args:
            org_id: ID numerik organisasi.
            asset_id: ID numerik aset yang akan diupdate.
            asset_code: Kode inventaris baru (opsional).
            asset_name: Nama baru (opsional).
            acquisition_cost: Harga perolehan baru dalam Rupiah (opsional).
            useful_life: Umur ekonomis baru dalam tahun (opsional).
            acquisition_year: Tahun perolehan baru (opsional).

        Returns:
            Dict data aset setelah diupdate, atau kunci ``error`` jika gagal.
        """
        payload: dict = {}
        if asset_code is not None:
            payload["asset_code"] = asset_code
        if asset_name is not None:
            payload["asset_name"] = asset_name
        if acquisition_cost is not None:
            payload["acquisition_cost"] = acquisition_cost
        if useful_life is not None:
            payload["useful_life"] = useful_life
        if acquisition_year is not None:
            payload["acquisition_year"] = acquisition_year

        response = await client.put(
            f"/organizations/{org_id}/depreciation/{asset_id}",
            json=payload,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Aset atau organization tidak ditemukan"}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_old_asset(org_id: int, asset_id: int) -> dict:
        """Hapus satu catatan aset tetap lama.

        Args:
            org_id: ID numerik organisasi.
            asset_id: ID numerik aset yang akan dihapus.

        Returns:
            Dict ``{"success": True}`` jika berhasil, atau kunci ``error`` jika gagal.
        """
        response = await client.delete(
            f"/organizations/{org_id}/depreciation/{asset_id}"
        )
        if response.status_code == 204:
            return {"success": True}
        if response.status_code == 404:
            return {"error": "Aset tidak ditemukan", "asset_id": asset_id}
        return {"error": response.text, "status_code": response.status_code}
