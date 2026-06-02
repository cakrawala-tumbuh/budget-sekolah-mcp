"""
Tool MCP untuk alokasi biaya dari Cabang/Pusat ke unit anak
(ParentExpenseAllocation).

Menyediakan tool CRUD untuk mendaftarkan kategori biaya tertentu dari
organisasi induk (CABANG atau PUSAT) yang dialokasikan ke unit-unit anaknya.
Hanya organisasi bertipe CABANG atau PUSAT yang dapat memiliki konfigurasi ini.

Tools yang tersedia:
  list_parent_expense_allocations  — Daftar alokasi biaya induk ke anak
  create_parent_expense_allocation — Tambah satu alokasi biaya
  update_parent_expense_allocation — Perbarui alokasi biaya (partial)
  delete_parent_expense_allocation — Hapus alokasi biaya

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool alokasi biaya induk ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_parent_expense_allocations(org_id: int) -> dict:
        """Daftar konfigurasi alokasi biaya dari organisasi induk ke unit anaknya.

        Hanya berlaku untuk organisasi bertipe CABANG atau PUSAT. Setiap entri
        menautkan satu kategori biaya yang dialokasikan ke unit-unit anak.

        Args:
            org_id: ID numerik organisasi CABANG atau PUSAT.

        Returns:
            Dict dengan kunci ``items`` berisi list alokasi, masing-masing
            memiliki ``id``, ``expense_category_id``, ``affects_up``,
            ``is_active``, ``expense_category_code``, dan ``expense_category_label``.
            Atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/parent-expense-allocations")
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {
                "error": "Alokasi biaya induk hanya berlaku untuk CABANG/PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def create_parent_expense_allocation(
        org_id: int,
        expense_category_id: int,
        affects_up: bool = False,
        is_active: bool = True,
    ) -> dict:
        """Tambah satu konfigurasi alokasi biaya dari induk ke unit anak.

        Daftarkan kategori biaya tertentu dari organisasi induk (CABANG/PUSAT)
        untuk dialokasikan ke unit-unit anaknya. Setiap pasangan
        (organisasi, kategori biaya) harus unik.

        Args:
            org_id: ID numerik organisasi CABANG atau PUSAT.
            expense_category_id: ID kategori biaya yang dialokasikan
                (lihat list_expense_categories).
            affects_up: Apakah alokasi ini ikut memengaruhi perhitungan UP
                (default False).
            is_active: Apakah alokasi aktif (default True).

        Returns:
            Dict data alokasi yang dibuat, atau kunci ``error`` jika gagal
            (mis. 409 jika kategori sudah dialokasikan untuk organisasi ini).
        """
        payload = {
            "expense_category_id": expense_category_id,
            "affects_up": affects_up,
            "is_active": is_active,
        }
        response = await client.post(
            f"/organizations/{org_id}/parent-expense-allocations", json=payload
        )
        if response.status_code == 201:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 409:
            return {
                "error": "Alokasi untuk kategori biaya ini sudah ada di organisasi ini",
                "org_id": org_id,
                "expense_category_id": expense_category_id,
            }
        if response.status_code == 422:
            return {
                "error": "Alokasi biaya induk hanya berlaku untuk CABANG/PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_parent_expense_allocation(
        org_id: int,
        alloc_id: int,
        affects_up: bool | None = None,
        is_active: bool | None = None,
    ) -> dict:
        """Perbarui satu konfigurasi alokasi biaya induk (partial update).

        Hanya field yang diisi yang akan diperbarui. Kategori biaya pada
        alokasi tidak dapat diubah — hapus lalu buat baru bila perlu.

        Args:
            org_id: ID numerik organisasi CABANG atau PUSAT pemilik alokasi.
            alloc_id: ID alokasi yang akan diperbarui.
            affects_up: Nilai baru untuk affects_up (None = tidak diubah).
            is_active: Nilai baru untuk is_active (None = tidak diubah).

        Returns:
            Dict data alokasi setelah diperbarui, atau kunci ``error`` jika gagal.
        """
        payload: dict = {}
        if affects_up is not None:
            payload["affects_up"] = affects_up
        if is_active is not None:
            payload["is_active"] = is_active

        response = await client.patch(
            f"/organizations/{org_id}/parent-expense-allocations/{alloc_id}",
            json=payload,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Allocation not found", "org_id": org_id, "alloc_id": alloc_id}
        if response.status_code == 422:
            return {
                "error": "Alokasi biaya induk hanya berlaku untuk CABANG/PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_parent_expense_allocation(org_id: int, alloc_id: int) -> dict:
        """Hapus satu konfigurasi alokasi biaya induk.

        Args:
            org_id: ID numerik organisasi CABANG atau PUSAT pemilik alokasi.
            alloc_id: ID alokasi yang akan dihapus.

        Returns:
            Dict ``{"success": True, "alloc_id": alloc_id}`` jika berhasil,
            atau kunci ``error`` jika gagal.
        """
        response = await client.delete(
            f"/organizations/{org_id}/parent-expense-allocations/{alloc_id}"
        )
        if response.status_code == 204:
            return {"success": True, "org_id": org_id, "alloc_id": alloc_id}
        if response.status_code == 404:
            return {"error": "Allocation not found", "org_id": org_id, "alloc_id": alloc_id}
        if response.status_code == 422:
            return {
                "error": "Alokasi biaya induk hanya berlaku untuk CABANG/PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}
