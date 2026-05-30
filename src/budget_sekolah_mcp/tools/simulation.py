"""
Tool MCP untuk menjalankan simulasi RAB.

Menyediakan tool untuk semua tipe simulasi yang tersedia di backend:
UP (Uang Pangkal), US (Uang Sekolah), income, expenses, allocation,
depreciation, dan summary.

Tools yang tersedia:
  simulate_up          — Simulasi komponen biaya Uang Pangkal (UNIT only)
  simulate_us          — Simulasi komponen biaya Uang Sekolah (UNIT only)
  simulate_income      — Simulasi total pendapatan semua akun
  simulate_expenses    — Simulasi total biaya operasional dan non-op
  simulate_allocation  — Simulasi penerimaan kontribusi dari bawah (CABANG/PUSAT only)
  simulate_depreciation — Simulasi total penyusutan aset
  simulate_summary     — Ringkasan lengkap RAB (Budget Kas & Akrual)

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool simulasi ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def simulate_up(org_id: int) -> dict:
        """Jalankan simulasi komponen Uang Pangkal (UP) untuk satu UNIT.

        Menghitung total biaya yang membentuk tarif UP, termasuk komponen
        dari akun 5130.xx (pengembangan SDM) dan depresiasi aset baru.

        Args:
            org_id: ID numerik organisasi UNIT.

        Returns:
            Dict hasil simulasi UP, termasuk kunci:
            - ``components``: list komponen biaya UP per akun
            - ``allocated_components``: komponen biaya UP dari organisasi induk
            - ``total_up_cost``: total biaya UP sebelum depresiasi
            - ``new_investment_dep``: depresiasi aset baru tahun berjalan
            - ``old_asset_dep``: depresiasi aset lama tahun berjalan
            - ``total_up_cost_with_dep``: total biaya UP termasuk depresiasi
            - ``new_student_count``: jumlah siswa baru
            - ``auto_up_rate``: tarif UP hasil kalkulasi
            - ``final_up_rate``: tarif UP final (pakai override jika ada)
            - ``total_up_revenue``: total pendapatan UP
            Atau kunci ``error`` jika gagal atau bukan UNIT.

        Example:
            >>> result = await simulate_up(org_id=3)
            >>> result["final_up_rate"]
            5000000.0
        """
        response = await client.get(f"/organizations/{org_id}/simulation/up")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {"error": "Simulasi UP hanya untuk organisasi UNIT", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def simulate_us(org_id: int) -> dict:
        """Jalankan simulasi komponen Uang Sekolah (US) untuk satu UNIT.

        Menghitung total biaya yang membentuk tarif US bulanan, yaitu
        seluruh biaya operasional kecuali komponen UP dan direct income accounts.

        Args:
            org_id: ID numerik organisasi UNIT.

        Returns:
            Dict hasil simulasi US, termasuk kunci:
            - ``components``: list komponen biaya US per akun
            - ``allocated_components``: komponen biaya US dari organisasi induk
            - ``total_us_cost``: total biaya US
            - ``total_students``: total semua siswa
            - ``months``: 12 (selalu)
            - ``auto_us_rate``: tarif US per bulan hasil kalkulasi
            - ``final_us_rate``: tarif US final (pakai override jika ada)
            - ``total_us_revenue``: total pendapatan US setahun
            Atau kunci ``error`` jika gagal atau bukan UNIT.

        Example:
            >>> result = await simulate_us(org_id=3)
            >>> result["final_us_rate"]
            450000.0
        """
        response = await client.get(f"/organizations/{org_id}/simulation/us")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {"error": "Simulasi US hanya untuk organisasi UNIT", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def simulate_income(org_id: int) -> dict:
        """Jalankan simulasi total pendapatan untuk satu organisasi.

        Menggabungkan semua akun pendapatan: UP, US, BOS, pendapatan manual,
        dan pendapatan lain-lain. Berlaku untuk semua tipe organisasi.

        Args:
            org_id: ID numerik organisasi (UNIT, CABANG, atau PUSAT).

        Returns:
            Dict hasil simulasi pendapatan, termasuk kunci:
            - ``items``: list item pendapatan per akun
            - ``total``: total pendapatan semua akun
            Atau kunci ``error`` jika gagal.

        Example:
            >>> result = await simulate_income(org_id=3)
            >>> result["total"]
            2500000000.0
        """
        response = await client.get(f"/organizations/{org_id}/simulation/income")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def simulate_expenses(org_id: int) -> dict:
        """Jalankan simulasi total biaya untuk satu organisasi.

        Menggabungkan semua akun biaya operasional (5110–5250) dan
        non-operasional (5500–5590). Berlaku untuk semua tipe organisasi.

        Args:
            org_id: ID numerik organisasi (UNIT, CABANG, atau PUSAT).

        Returns:
            Dict hasil simulasi biaya, termasuk kunci:
            - ``operational``: list biaya operasional per akun
            - ``non_operational``: list biaya non-operasional per akun
            - ``total_operational``: total biaya operasional
            - ``total_non_operational``: total biaya non-operasional
            - ``grand_total``: total semua biaya
            Atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/simulation/expenses")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def simulate_allocation(org_id: int) -> dict:
        """Jalankan simulasi penerimaan kontribusi dari bawah (CABANG/PUSAT only).

        Menghitung berapa total kontribusi UP dan US yang diterima dari
        unit/cabang di bawah organisasi ini, berdasarkan alokasi yang terdaftar.

        Args:
            org_id: ID numerik organisasi CABANG atau PUSAT.

        Returns:
            Dict hasil simulasi alokasi kontribusi,
            atau kunci ``error`` jika gagal atau bukan CABANG/PUSAT.
        """
        response = await client.get(f"/organizations/{org_id}/simulation/allocation")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {"error": "Simulasi alokasi hanya untuk CABANG/PUSAT", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def simulate_depreciation(org_id: int) -> dict:
        """Jalankan simulasi ringkasan penyusutan aset untuk satu organisasi.

        Menggabungkan depresiasi aset baru (proporsional) dan aset lama
        (garis lurus). Berlaku untuk semua tipe organisasi.

        Args:
            org_id: ID numerik organisasi.

        Returns:
            Dict ringkasan depresiasi, termasuk:
            - ``new_assets``: list aset baru dengan dep tahun berjalan
            - ``old_assets``: list aset lama dengan dep per tahun
            - ``total_new_dep``: total depresiasi aset baru
            - ``total_old_dep``: total depresiasi aset lama
            - ``grand_total``: total semua depresiasi
            Atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/simulation/depreciation")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def simulate_summary(org_id: int) -> dict:
        """Jalankan simulasi ringkasan lengkap RAB (Budget Kas & Akrual).

        Menghasilkan ringkasan akhir anggaran yang mencakup total pendapatan,
        total biaya, surplus/defisit, dan perbandingan kas vs akrual.
        Berlaku untuk semua tipe organisasi.

        Args:
            org_id: ID numerik organisasi (UNIT, CABANG, atau PUSAT).

        Returns:
            Dict ringkasan lengkap RAB, termasuk:
            - ``total_income``: total pendapatan
            - ``total_expense``: total biaya
            - ``surplus_deficit``: selisih (positif = surplus)
            - ``cash_budget``: ringkasan Budget Kas
            - ``accrual_budget``: ringkasan Budget Akrual
            Atau kunci ``error`` jika gagal.

        Example:
            >>> result = await simulate_summary(org_id=3)
            >>> result["surplus_deficit"]
            150000000.0
        """
        response = await client.get(f"/organizations/{org_id}/simulation/summary")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}
