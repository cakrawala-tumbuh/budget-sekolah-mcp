"""
Tool MCP untuk entri pendapatan manual.

Menyediakan tool CRUD untuk IncomeEntry — baris rincian pendapatan yang
diisi manual (bukan yang dihitung otomatis oleh formula template seperti
UP, US, dan BOS).

Tools yang tersedia:
  list_income_entries        — Daftar entri pendapatan
  create_income_entry        — Tambah satu baris pendapatan manual
  bulk_create_income_entries — Tambah banyak baris pendapatan sekaligus
  update_income_entry        — Update satu baris pendapatan
  delete_income_entry        — Hapus satu baris pendapatan

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool income entries ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_income_entries(org_id: int, category_id: int | None = None) -> dict:
        """Ambil daftar entri pendapatan manual untuk satu organisasi.

        Hanya mengembalikan pendapatan yang diisi manual. Pendapatan yang
        dihitung otomatis (UP, US, BOS) tidak muncul di sini — gunakan
        simulate_income untuk melihat total pendapatan lengkap.

        Args:
            org_id: ID numerik organisasi.
            category_id: Filter berdasarkan ID kategori pendapatan (opsional).

        Returns:
            Dict dengan kunci ``items`` berisi list entri pendapatan,
            atau kunci ``error`` jika gagal.
        """
        params: dict = {}
        if category_id is not None:
            params["category_id"] = category_id
        response = await client.get(f"/organizations/{org_id}/income-entries", params=params)
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def create_income_entry(
        org_id: int,
        income_category_id: int,
        line_number: int = 1,
        description: str | None = None,
        basis: str | None = None,
        amount: float = 0.0,
        notes: str | None = None,
    ) -> dict:
        """Tambah satu baris pendapatan manual ke satu organisasi.

        Args:
            org_id: ID numerik organisasi.
            income_category_id: ID kategori pendapatan (akun seperti 4120.03).
            line_number: Nomor urut baris dalam satu akun (default: 1).
            description: Deskripsi sumber pendapatan.
            basis: Dasar perhitungan (contoh: "316 siswa × Rp 100.000").
            amount: Jumlah pendapatan dalam Rupiah.
            notes: Catatan tambahan (opsional).

        Returns:
            Dict data entri yang dibuat, atau kunci ``error`` jika gagal.
        """
        payload = {
            "income_category_id": income_category_id,
            "line_number": line_number,
            "description": description,
            "basis": basis,
            "amount": amount,
            "notes": notes,
        }
        response = await client.post(f"/organizations/{org_id}/income-entries", json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def bulk_create_income_entries(org_id: int, entries: list[dict]) -> dict:
        """Tambah banyak baris pendapatan manual sekaligus.

        Args:
            org_id: ID numerik organisasi.
            entries: List dict, masing-masing berisi field entri pendapatan:
                     ``income_category_id``, ``line_number``, ``description``,
                     ``basis``, ``amount``, ``notes``.

        Returns:
            Dict dengan kunci ``items`` berisi list entri yang dibuat,
            atau kunci ``error`` jika gagal.
        """
        response = await client.post(
            f"/organizations/{org_id}/income-entries/bulk",
            json={"entries": entries},
        )
        if response.status_code == 201:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_income_entry(
        org_id: int,
        entry_id: int,
        description: str | None = None,
        basis: str | None = None,
        amount: float | None = None,
        notes: str | None = None,
    ) -> dict:
        """Update satu baris pendapatan manual yang sudah ada.

        Args:
            org_id: ID numerik organisasi.
            entry_id: ID numerik baris entri yang akan diupdate.
            description: Deskripsi baru (opsional).
            basis: Dasar perhitungan baru (opsional).
            amount: Jumlah baru dalam Rupiah (opsional).
            notes: Catatan baru (opsional).

        Returns:
            Dict data entri setelah diupdate, atau kunci ``error`` jika gagal.
        """
        payload: dict = {}
        if description is not None:
            payload["description"] = description
        if basis is not None:
            payload["basis"] = basis
        if amount is not None:
            payload["amount"] = amount
        if notes is not None:
            payload["notes"] = notes

        response = await client.put(
            f"/organizations/{org_id}/income-entries/{entry_id}",
            json=payload,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Entry atau organization tidak ditemukan", "entry_id": entry_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_income_entry(org_id: int, entry_id: int) -> dict:
        """Hapus satu baris pendapatan manual.

        Args:
            org_id: ID numerik organisasi.
            entry_id: ID numerik baris yang akan dihapus.

        Returns:
            Dict ``{"success": True}`` jika berhasil, atau kunci ``error`` jika gagal.
        """
        response = await client.delete(
            f"/organizations/{org_id}/income-entries/{entry_id}"
        )
        if response.status_code == 204:
            return {"success": True}
        if response.status_code == 404:
            return {"error": "Entry tidak ditemukan", "entry_id": entry_id}
        return {"error": response.text, "status_code": response.status_code}
