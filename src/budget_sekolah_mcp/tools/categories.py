"""
Tool MCP untuk membaca daftar kategori (read-only).

Menyediakan tool untuk mengambil daftar kategori biaya, pendapatan,
dan investasi yang di-seed otomatis oleh backend saat startup.
Data ini dibutuhkan untuk mengetahui ``id`` kategori sebelum membuat
entri anggaran.

Tools yang tersedia:
  list_expense_categories    — Daftar kategori biaya (akun 5110–5590)
  create_expense_category    — Buat kategori biaya baru (admin)
  update_expense_category    — Ubah flag/atribut kategori biaya (admin)
  delete_expense_category    — Hapus kategori biaya (admin)
  list_income_categories     — Daftar kategori pendapatan (akun 4110–4620)
  list_investment_categories — Daftar kategori investasi (akun 1330.01–1330.08)

Catatan: kategori biaya adalah data referensi GLOBAL (dipakai semua
organisasi). Mengubah flag seperti ``is_operational`` memengaruhi
perhitungan UP/US untuk SELURUH organisasi, bukan satu unit saja.
Operasi tulis (create/update/delete) memerlukan akses admin.

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

    @mcp.tool()
    async def create_expense_category(
        code: str,
        label: str,
        is_operational: bool = True,
        is_up_component: bool = False,
        is_direct_income: bool = False,
        maps_to_income_category_id: int | None = None,
        contribution_role: str | None = None,
        sort_order: int = 0,
    ) -> dict:
        """Buat kategori biaya baru (membutuhkan akses admin).

        Kategori biaya bersifat GLOBAL — begitu dibuat, tersedia untuk semua
        organisasi. Flag menentukan bagaimana biaya diperhitungkan:
        ``is_up_component`` (masuk Uang Pangkal), ``is_operational`` (masuk
        Uang Sekolah bila bukan UP & bukan direct income), ``is_direct_income``
        (langsung menghasilkan pendapatan, butuh ``maps_to_income_category_id``).

        Args:
            code: Kode akun unik (mis. "5260.01").
            label: Nama/keterangan kategori.
            is_operational: Biaya operasional → masuk US (default True).
            is_up_component: Komponen Uang Pangkal → masuk UP (default False).
            is_direct_income: Biaya yang langsung jadi pendapatan (default False).
            maps_to_income_category_id: ID kategori pendapatan tujuan bila
                ``is_direct_income`` True (opsional).
            contribution_role: Peran kontribusi khusus, bila ada (opsional).
            sort_order: Urutan tampil (default 0).

        Returns:
            Dict data kategori yang dibuat, atau kunci ``error`` jika gagal
            (mis. 409 bila ``code`` sudah ada, 403 bila bukan admin).
        """
        payload: dict = {
            "code": code,
            "label": label,
            "is_operational": is_operational,
            "is_up_component": is_up_component,
            "is_direct_income": is_direct_income,
            "maps_to_income_category_id": maps_to_income_category_id,
            "contribution_role": contribution_role,
            "sort_order": sort_order,
        }
        response = await client.post("/expense-categories", json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 409:
            return {"error": f"Kategori dengan kode '{code}' sudah ada", "code": code}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_expense_category(
        category_id: int,
        label: str | None = None,
        is_operational: bool | None = None,
        is_up_component: bool | None = None,
        is_direct_income: bool | None = None,
        maps_to_income_category_id: int | None = None,
        contribution_role: str | None = None,
        sort_order: int | None = None,
    ) -> dict:
        """Ubah atribut/flag satu kategori biaya (partial update, admin).

        Hanya field yang diisi yang diperbarui. PERHATIAN: kategori biaya
        GLOBAL — mengubah flag memengaruhi perhitungan UP/US untuk SEMUA
        organisasi yang memakai kategori ini, bukan satu unit saja. Contoh
        kasus: menjadikan kategori non-operasional (mis. 5580.xx sumbangan/
        beasiswa) ikut perhitungan US → set ``is_operational=True``.

        Args:
            category_id: ID kategori biaya yang diubah
                (lihat list_expense_categories untuk ``id``).
            label: Nama baru (None = tidak diubah).
            is_operational: True → masuk US; False → non-operasional
                (None = tidak diubah).
            is_up_component: True → masuk UP (None = tidak diubah).
            is_direct_income: True → biaya langsung jadi pendapatan
                (None = tidak diubah).
            maps_to_income_category_id: ID kategori pendapatan tujuan untuk
                direct income (None = tidak diubah).
            contribution_role: Peran kontribusi khusus (None = tidak diubah).
            sort_order: Urutan tampil baru (None = tidak diubah).

        Returns:
            Dict data kategori setelah diperbarui, atau kunci ``error`` jika
            gagal (mis. 404 bila tidak ditemukan, 403 bila bukan admin).
        """
        payload: dict = {}
        if label is not None:
            payload["label"] = label
        if is_operational is not None:
            payload["is_operational"] = is_operational
        if is_up_component is not None:
            payload["is_up_component"] = is_up_component
        if is_direct_income is not None:
            payload["is_direct_income"] = is_direct_income
        if maps_to_income_category_id is not None:
            payload["maps_to_income_category_id"] = maps_to_income_category_id
        if contribution_role is not None:
            payload["contribution_role"] = contribution_role
        if sort_order is not None:
            payload["sort_order"] = sort_order

        response = await client.put(f"/expense-categories/{category_id}", json=payload)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Expense category not found", "category_id": category_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_expense_category(category_id: int) -> dict:
        """Hapus satu kategori biaya (membutuhkan akses admin).

        PERHATIAN: kategori GLOBAL. Menghapus kategori yang masih dipakai
        entri anggaran dapat ditolak backend. Pertimbangkan menonaktifkan
        lewat flag daripada menghapus.

        Args:
            category_id: ID kategori biaya yang akan dihapus.

        Returns:
            Dict ``{"success": True, "category_id": category_id}`` jika
            berhasil, atau kunci ``error`` jika gagal.
        """
        response = await client.delete(f"/expense-categories/{category_id}")
        if response.status_code == 204:
            return {"success": True, "category_id": category_id}
        if response.status_code == 404:
            return {"error": "Expense category not found", "category_id": category_id}
        return {"error": response.text, "status_code": response.status_code}
