"""
Tool MCP untuk entri anggaran biaya (operasional dan non-operasional).

Menyediakan tool CRUD untuk BudgetEntry — baris rincian biaya yang terikat
ke satu ExpenseCategory dalam satu organisasi.

Tools yang tersedia:
  list_budget_entries              — Daftar entri biaya (bisa difilter per kategori)
  create_budget_entry              — Tambah satu baris rincian biaya
  bulk_create_budget_entries       — Tambah banyak baris sekaligus
  update_budget_entry              — Update satu baris rincian
  delete_budget_entry              — Hapus satu baris rincian
  delete_budget_entries_by_category — Hapus semua baris pada satu kategori

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool budget entries ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_budget_entries(org_id: int, category_id: int | None = None) -> dict:
        """Ambil daftar entri anggaran biaya untuk satu organisasi.

        Args:
            org_id: ID numerik organisasi.
            category_id: Filter berdasarkan ID kategori biaya (opsional).
                         Jika tidak diisi, kembalikan semua entri.

        Returns:
            Dict dengan kunci ``items`` berisi list entri biaya,
            atau kunci ``error`` jika gagal.

        Example:
            >>> result = await list_budget_entries(org_id=3, category_id=5)
            >>> len(result["items"])
            3
        """
        params: dict = {}
        if category_id is not None:
            params["category_id"] = category_id
        response = await client.get(f"/organizations/{org_id}/budget-entries", params=params)
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def create_budget_entry(
        org_id: int,
        expense_category_id: int,
        line_number: int = 1,
        description: str | None = None,
        basis: str | None = None,
        foundation: float = 0.0,
        bos: float = 0.0,
        notes: str | None = None,
    ) -> dict:
        """Tambah satu baris rincian biaya ke satu organisasi.

        Args:
            org_id: ID numerik organisasi.
            expense_category_id: ID kategori biaya (akun seperti 5110.01).
            line_number: Nomor urut baris rincian dalam satu akun (default: 1).
            description: Deskripsi rincian biaya.
            basis: Dasar perhitungan (contoh: "24 org × Rp 3.500.000 × 12 bln").
            foundation: Nilai biaya yang ditanggung Yayasan (Rp).
            bos: Nilai biaya dari dana BOS/BOP/PBOS (Rp).
            notes: Catatan tambahan (opsional).

        Returns:
            Dict data entri yang dibuat, atau kunci ``error`` jika gagal.
        """
        payload = {
            "expense_category_id": expense_category_id,
            "line_number": line_number,
            "description": description,
            "basis": basis,
            "foundation": foundation,
            "bos": bos,
            "notes": notes,
        }
        response = await client.post(f"/organizations/{org_id}/budget-entries", json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def bulk_create_budget_entries(org_id: int, entries: list[dict]) -> dict:
        """Tambah banyak baris rincian biaya sekaligus untuk satu organisasi.

        Lebih efisien daripada memanggil create_budget_entry berulang kali.
        Semua entri diproses dalam satu request HTTP.

        Args:
            org_id: ID numerik organisasi.
            entries: List dict, masing-masing berisi field entri biaya:
                     ``expense_category_id``, ``line_number``, ``description``,
                     ``basis``, ``foundation``, ``bos``, ``notes``.

        Returns:
            Dict dengan kunci ``items`` berisi list entri yang dibuat,
            atau kunci ``error`` jika gagal.

        Example:
            >>> entries = [
            ...     {"expense_category_id": 1, "line_number": 1,
            ...      "description": "Gaji guru", "foundation": 1000000, "bos": 0},
            ... ]
            >>> result = await bulk_create_budget_entries(org_id=3, entries=entries)
        """
        response = await client.post(
            f"/organizations/{org_id}/budget-entries/bulk",
            json={"entries": entries},
        )
        if response.status_code == 201:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_budget_entry(
        org_id: int,
        entry_id: int,
        description: str | None = None,
        basis: str | None = None,
        foundation: float | None = None,
        bos: float | None = None,
        notes: str | None = None,
    ) -> dict:
        """Update satu baris rincian biaya yang sudah ada.

        Hanya field yang diisi yang akan diperbarui (partial update).

        Args:
            org_id: ID numerik organisasi.
            entry_id: ID numerik baris entri yang akan diupdate.
            description: Deskripsi baru (opsional).
            basis: Dasar perhitungan baru (opsional).
            foundation: Nilai Yayasan baru dalam Rupiah (opsional).
            bos: Nilai BOS baru dalam Rupiah (opsional).
            notes: Catatan baru (opsional).

        Returns:
            Dict data entri setelah diupdate, atau kunci ``error`` jika gagal.
        """
        payload: dict = {}
        if description is not None:
            payload["description"] = description
        if basis is not None:
            payload["basis"] = basis
        if foundation is not None:
            payload["foundation"] = foundation
        if bos is not None:
            payload["bos"] = bos
        if notes is not None:
            payload["notes"] = notes

        response = await client.put(
            f"/organizations/{org_id}/budget-entries/{entry_id}",
            json=payload,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Entry atau organization tidak ditemukan", "entry_id": entry_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_budget_entry(org_id: int, entry_id: int) -> dict:
        """Hapus satu baris rincian biaya.

        Args:
            org_id: ID numerik organisasi.
            entry_id: ID numerik baris yang akan dihapus.

        Returns:
            Dict ``{"success": True}`` jika berhasil, atau kunci ``error`` jika gagal.
        """
        response = await client.delete(
            f"/organizations/{org_id}/budget-entries/{entry_id}"
        )
        if response.status_code == 204:
            return {"success": True}
        if response.status_code == 404:
            return {"error": "Entry tidak ditemukan", "entry_id": entry_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_budget_entries_by_category(org_id: int, category_id: int) -> dict:
        """Hapus semua baris rincian biaya pada satu kategori akun.

        Berguna untuk reset data satu akun sebelum mengisi ulang.

        Args:
            org_id: ID numerik organisasi.
            category_id: ID kategori biaya yang seluruh entrinya akan dihapus.

        Returns:
            Dict ``{"success": True}`` jika berhasil, atau kunci ``error`` jika gagal.
        """
        response = await client.delete(
            f"/organizations/{org_id}/budget-entries/by-category/{category_id}"
        )
        if response.status_code == 204:
            return {"success": True}
        if response.status_code == 404:
            return {"error": "Organization atau kategori tidak ditemukan"}
        return {"error": response.text, "status_code": response.status_code}
