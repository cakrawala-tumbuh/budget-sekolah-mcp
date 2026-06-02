"""
Tool MCP untuk subsidi dari Cabang/Pusat ke unit penerima (Subsidy).

Menyediakan tool CRUD untuk mengelola subsidi yang diberikan organisasi
pemberi (CABANG atau PUSAT) kepada organisasi penerima.

Aturan keterhubungan:
  - CABANG hanya dapat memberi subsidi ke UNIT anaknya.
  - PUSAT dapat memberi subsidi ke CABANG atau UNIT mana pun.

Tools yang tersedia:
  list_subsidies  — Daftar subsidi dari satu organisasi pemberi
  create_subsidy  — Tambah subsidi ke penerima
  update_subsidy  — Perbarui subsidi (partial)
  delete_subsidy  — Hapus subsidi

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool subsidi ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_subsidies(org_id: int) -> dict:
        """Daftar subsidi yang diberikan satu organisasi ke para penerimanya.

        Hanya berlaku untuk organisasi pemberi bertipe CABANG atau PUSAT.

        Args:
            org_id: ID numerik organisasi pemberi (CABANG atau PUSAT).

        Returns:
            Dict dengan kunci ``items`` berisi list subsidi, masing-masing
            memiliki ``id``, ``recipient_org_id``, ``recipient_org_name``,
            ``expense_category_id``, ``income_category_id``, ``amount``,
            ``is_active``, beserta kode/label kategori biaya dan pendapatan.
            Atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/subsidies")
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {
                "error": "Subsidi hanya dapat diberikan oleh organisasi CABANG atau PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def create_subsidy(
        org_id: int,
        recipient_org_id: int,
        expense_category_id: int,
        income_category_id: int,
        amount: float = 0.0,
        is_active: bool = True,
    ) -> dict:
        """Tambah satu subsidi dari organisasi pemberi ke penerima.

        Subsidi mencatat dana yang dialirkan dari pemberi (CABANG/PUSAT) ke
        organisasi penerima: muncul sebagai biaya pada pemberi (expense_category)
        dan sebagai pendapatan pada penerima (income_category).

        Aturan penerima:
          - CABANG hanya dapat memberi subsidi ke UNIT anaknya.
          - PUSAT dapat memberi subsidi ke CABANG atau UNIT mana pun.

        Args:
            org_id: ID numerik organisasi pemberi (CABANG atau PUSAT).
            recipient_org_id: ID organisasi penerima subsidi.
            expense_category_id: ID kategori biaya pada sisi pemberi
                (lihat list_expense_categories).
            income_category_id: ID kategori pendapatan pada sisi penerima
                (lihat list_income_categories).
            amount: Nominal subsidi dalam Rupiah (default 0.0).
            is_active: Apakah subsidi aktif (default True).

        Returns:
            Dict data subsidi yang dibuat, atau kunci ``error`` jika gagal
            (mis. 422 jika penerima tidak valid sesuai aturan keterhubungan).
        """
        payload = {
            "recipient_org_id": recipient_org_id,
            "expense_category_id": expense_category_id,
            "income_category_id": income_category_id,
            "amount": amount,
            "is_active": is_active,
        }
        response = await client.post(f"/organizations/{org_id}/subsidies", json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organisasi pemberi atau penerima tidak ditemukan", "org_id": org_id}
        if response.status_code == 422:
            return {
                "error": "Penerima tidak valid atau pemberi bukan CABANG/PUSAT",
                "org_id": org_id,
                "detail": response.text,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_subsidy(
        org_id: int,
        subsidy_id: int,
        recipient_org_id: int | None = None,
        expense_category_id: int | None = None,
        income_category_id: int | None = None,
        amount: float | None = None,
        is_active: bool | None = None,
    ) -> dict:
        """Perbarui satu subsidi (partial update).

        Hanya field yang diisi yang akan diperbarui. Jika ``recipient_org_id``
        diubah, penerima baru akan divalidasi ulang sesuai aturan keterhubungan.

        Args:
            org_id: ID numerik organisasi pemberi pemilik subsidi.
            subsidy_id: ID subsidi yang akan diperbarui.
            recipient_org_id: ID penerima baru (None = tidak diubah).
            expense_category_id: ID kategori biaya baru (None = tidak diubah).
            income_category_id: ID kategori pendapatan baru (None = tidak diubah).
            amount: Nominal baru dalam Rupiah (None = tidak diubah).
            is_active: Status aktif baru (None = tidak diubah).

        Returns:
            Dict data subsidi setelah diperbarui, atau kunci ``error`` jika gagal.
        """
        payload: dict = {}
        if recipient_org_id is not None:
            payload["recipient_org_id"] = recipient_org_id
        if expense_category_id is not None:
            payload["expense_category_id"] = expense_category_id
        if income_category_id is not None:
            payload["income_category_id"] = income_category_id
        if amount is not None:
            payload["amount"] = amount
        if is_active is not None:
            payload["is_active"] = is_active

        response = await client.patch(
            f"/organizations/{org_id}/subsidies/{subsidy_id}", json=payload
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Subsidi tidak ditemukan", "org_id": org_id, "subsidy_id": subsidy_id}
        if response.status_code == 422:
            return {
                "error": "Penerima tidak valid atau pemberi bukan CABANG/PUSAT",
                "org_id": org_id,
                "detail": response.text,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_subsidy(org_id: int, subsidy_id: int) -> dict:
        """Hapus satu subsidi.

        Args:
            org_id: ID numerik organisasi pemberi pemilik subsidi.
            subsidy_id: ID subsidi yang akan dihapus.

        Returns:
            Dict ``{"success": True, "subsidy_id": subsidy_id}`` jika berhasil,
            atau kunci ``error`` jika gagal.
        """
        response = await client.delete(f"/organizations/{org_id}/subsidies/{subsidy_id}")
        if response.status_code == 204:
            return {"success": True, "org_id": org_id, "subsidy_id": subsidy_id}
        if response.status_code == 404:
            return {"error": "Subsidi tidak ditemukan", "org_id": org_id, "subsidy_id": subsidy_id}
        if response.status_code == 422:
            return {
                "error": "Subsidi hanya dapat diberikan oleh organisasi CABANG atau PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}
