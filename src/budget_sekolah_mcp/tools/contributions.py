"""
Tool MCP untuk tarif kontribusi dan alokasi kontribusi antar organisasi.

Menyediakan tool untuk mengelola tarif kontribusi (persentase UP/US yang
disetor ke CABANG dan PUSAT) serta alokasi kontribusi dari UNIT/CABANG
ke organisasi induknya.

Tools yang tersedia:
  get_contribution_rates        — Baca tarif kontribusi satu organisasi
  set_contribution_rates        — Set tarif kontribusi satu organisasi
  list_contribution_allocations — Daftar alokasi kontribusi (CABANG/PUSAT)
  upsert_contribution_allocation — Set atau perbarui satu alokasi kontribusi

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool kontribusi ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def get_contribution_rates(org_id: int) -> dict:
        """Baca tarif kontribusi yang berlaku untuk satu organisasi.

        Tarif kontribusi menentukan berapa persen dari UP dan US yang
        disetor ke organisasi CABANG dan PUSAT.

        Args:
            org_id: ID numerik organisasi.

        Returns:
            Dict berisi semua tarif (nilai 0.0–1.0), termasuk kunci:
            - ``up_to_pusat``: % UP ke Pusat (default 4%)
            - ``up_to_cabang``: % UP ke Cabang (default 12%)
            - ``us_to_pusat``: % US ke Pusat (default 5%)
            - ``us_to_cabang``: % US ke Cabang (default 10%)
            - ``development_fund``: % Dana Pembangunan (default 20%)
            - ``deficit_reserve``: % Cadangan Karya Defisit (default 5%)
            - ``social_care``: % Kepedulian Sosial (default 3%)
            - ``teacher_study``: % Studi Guru/Karyawan (default 3%)
            Atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/contribution-rates")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def set_contribution_rates(
        org_id: int,
        up_to_pusat: float = 0.04,
        up_to_cabang: float = 0.12,
        us_to_pusat: float = 0.05,
        us_to_cabang: float = 0.10,
        development_fund: float = 0.20,
        deficit_reserve: float = 0.05,
        social_care: float = 0.03,
        teacher_study: float = 0.03,
    ) -> dict:
        """Set semua tarif kontribusi untuk satu organisasi sekaligus.

        Semua tarif ditetapkan sebagai nilai desimal (0.0–1.0), bukan persen.
        Contoh: 4% dimasukkan sebagai 0.04.

        Args:
            org_id: ID numerik organisasi.
            up_to_pusat: Persentase UP yang disetor ke Pusat (default 0.04).
            up_to_cabang: Persentase UP yang disetor ke Cabang (default 0.12).
            us_to_pusat: Persentase US yang disetor ke Pusat (default 0.05).
            us_to_cabang: Persentase US yang disetor ke Cabang (default 0.10).
            development_fund: Persentase Dana Pembangunan (default 0.20).
            deficit_reserve: Persentase Cadangan Karya Defisit (default 0.05).
            social_care: Persentase Program Kepedulian Sosial (default 0.03).
            teacher_study: Persentase Studi Guru/Karyawan (default 0.03).

        Returns:
            Dict tarif kontribusi setelah disimpan, atau kunci ``error`` jika gagal.
        """
        payload = {
            "up_to_pusat": up_to_pusat,
            "up_to_cabang": up_to_cabang,
            "us_to_pusat": us_to_pusat,
            "us_to_cabang": us_to_cabang,
            "development_fund": development_fund,
            "deficit_reserve": deficit_reserve,
            "social_care": social_care,
            "teacher_study": teacher_study,
        }
        response = await client.put(f"/organizations/{org_id}/contribution-rates", json=payload)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def list_contribution_allocations(org_id: int) -> dict:
        """Daftar alokasi kontribusi dari unit/cabang ke organisasi ini.

        Hanya berlaku untuk organisasi bertipe CABANG atau PUSAT.

        Args:
            org_id: ID numerik organisasi CABANG atau PUSAT.

        Returns:
            Dict dengan kunci ``items`` berisi list alokasi kontribusi,
            atau kunci ``error`` jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/contribution-allocations")
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {
                "error": "Alokasi kontribusi hanya berlaku untuk CABANG/PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def upsert_contribution_allocation(
        org_id: int,
        from_organization_id: int,
        total_students: int = 0,
        new_students: int = 0,
        override_pct_us: float | None = None,
        override_pct_up: float | None = None,
    ) -> dict:
        """Set atau perbarui alokasi kontribusi dari satu unit/cabang ke organisasi ini.

        Digunakan untuk mendaftarkan berapa jumlah siswa dari organisasi sumber
        yang berkontribusi ke CABANG atau PUSAT ini.

        Args:
            org_id: ID numerik organisasi CABANG atau PUSAT yang menerima kontribusi.
            from_organization_id: ID organisasi sumber kontribusi (UNIT atau CABANG).
            total_students: Total siswa dari organisasi sumber.
            new_students: Jumlah siswa baru dari organisasi sumber.
            override_pct_us: Override persentase kontribusi US (None = pakai default).
            override_pct_up: Override persentase kontribusi UP (None = pakai default).

        Returns:
            Dict data alokasi yang dibuat/diperbarui, atau kunci ``error`` jika gagal.
        """
        payload: dict = {
            "from_organization_id": from_organization_id,
            "total_students": total_students,
            "new_students": new_students,
            "override_pct_us": override_pct_us,
            "override_pct_up": override_pct_up,
        }
        response = await client.put(
            f"/organizations/{org_id}/contribution-allocations",
            json=payload,
        )
        if response.status_code in (200, 201):
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {
                "error": "Alokasi kontribusi hanya berlaku untuk CABANG/PUSAT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}
