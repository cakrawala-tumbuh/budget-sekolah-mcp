"""
Tool MCP untuk asumsi satuan pendidikan (UNIT only).

Menyediakan tool untuk membaca dan mengatur asumsi jumlah siswa, staf,
serta override tarif UP/US/kegiatan untuk organisasi bertipe UNIT.

Tools yang tersedia:
  get_assumption    — Baca asumsi siswa untuk satu UNIT
  upsert_assumption — Set atau perbarui asumsi siswa untuk satu UNIT
  delete_assumption — Hapus asumsi siswa untuk satu UNIT

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool asumsi ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def get_assumption(org_id: int) -> dict:
        """Baca asumsi jumlah siswa dan staf untuk satu organisasi UNIT.

        Asumsi mencakup jumlah siswa per kelas, jumlah siswa baru/lama,
        jumlah staf, dan override tarif UP/US/kegiatan jika ada.

        Args:
            org_id: ID numerik organisasi UNIT.

        Returns:
            Dict berisi asumsi siswa, termasuk kunci:
            - ``grade_1`` s/d ``grade_6``: jumlah siswa per kelas
            - ``new_student_count``: jumlah siswa baru
            - ``returning_student_count``: jumlah siswa lama
            - ``staff_count``: jumlah guru dan karyawan
            - ``total_students``: total semua siswa
            - ``override_up_rate``: tarif UP manual (null = otomatis)
            - ``override_us_rate``: tarif US manual (null = otomatis)
            Atau kunci ``error`` jika tidak ditemukan.

        Example:
            >>> result = await get_assumption(org_id=3)
            >>> result["total_students"]
            336
        """
        response = await client.get(f"/organizations/{org_id}/assumption")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Asumsi belum diisi atau organisasi tidak ditemukan", "org_id": org_id}
        if response.status_code == 422:
            return {"error": "Asumsi hanya berlaku untuk organisasi UNIT", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def upsert_assumption(
        org_id: int,
        grade_1: int = 0,
        grade_2: int = 0,
        grade_3: int = 0,
        grade_4: int = 0,
        grade_5: int = 0,
        grade_6: int = 0,
        new_student_count: int = 0,
        returning_student_count: int = 0,
        staff_count: int = 0,
        override_up_rate: float | None = None,
        override_us_rate: float | None = None,
        override_activity_grade_1: float | None = None,
        override_activity_grade_2: float | None = None,
        override_activity_grade_3: float | None = None,
        override_activity_grade_4: float | None = None,
        override_activity_grade_5: float | None = None,
        override_activity_grade_6: float | None = None,
    ) -> dict:
        """Set atau perbarui asumsi siswa untuk satu organisasi UNIT.

        Jika asumsi belum ada, akan dibuat baru. Jika sudah ada, akan diperbarui
        seluruhnya (bukan partial update — semua field dikirim sekaligus).

        Override tarif bersifat opsional: biarkan None agar tarif dihitung
        otomatis dari simulasi biaya.

        Args:
            org_id: ID numerik organisasi UNIT.
            grade_1: Jumlah siswa kelas 1.
            grade_2: Jumlah siswa kelas 2.
            grade_3: Jumlah siswa kelas 3.
            grade_4: Jumlah siswa kelas 4.
            grade_5: Jumlah siswa kelas 5.
            grade_6: Jumlah siswa kelas 6.
            new_student_count: Jumlah siswa baru (masuk kelas 1).
            returning_student_count: Jumlah siswa yang naik kelas.
            staff_count: Jumlah guru dan karyawan aktif.
            override_up_rate: Override tarif UP manual dalam Rupiah (None = otomatis).
            override_us_rate: Override tarif US per bulan dalam Rupiah (None = otomatis).
            override_activity_grade_1: Override tarif kegiatan kelas 1 (None = otomatis).
            override_activity_grade_2: Override tarif kegiatan kelas 2 (None = otomatis).
            override_activity_grade_3: Override tarif kegiatan kelas 3 (None = otomatis).
            override_activity_grade_4: Override tarif kegiatan kelas 4 (None = otomatis).
            override_activity_grade_5: Override tarif kegiatan kelas 5 (None = otomatis).
            override_activity_grade_6: Override tarif kegiatan kelas 6 (None = otomatis).

        Returns:
            Dict data asumsi setelah disimpan, atau kunci ``error`` jika gagal.
        """
        payload = {
            "grade_1": grade_1,
            "grade_2": grade_2,
            "grade_3": grade_3,
            "grade_4": grade_4,
            "grade_5": grade_5,
            "grade_6": grade_6,
            "new_student_count": new_student_count,
            "returning_student_count": returning_student_count,
            "staff_count": staff_count,
            "override_up_rate": override_up_rate,
            "override_us_rate": override_us_rate,
            "override_activity_grade_1": override_activity_grade_1,
            "override_activity_grade_2": override_activity_grade_2,
            "override_activity_grade_3": override_activity_grade_3,
            "override_activity_grade_4": override_activity_grade_4,
            "override_activity_grade_5": override_activity_grade_5,
            "override_activity_grade_6": override_activity_grade_6,
        }
        response = await client.put(f"/organizations/{org_id}/assumption", json=payload)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {"error": "Asumsi hanya berlaku untuk organisasi UNIT", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_assumption(org_id: int) -> dict:
        """Hapus asumsi siswa untuk satu organisasi UNIT.

        Args:
            org_id: ID numerik organisasi UNIT.

        Returns:
            Dict ``{"success": True, "org_id": org_id}`` jika berhasil,
            atau kunci ``error`` jika gagal.
        """
        response = await client.delete(f"/organizations/{org_id}/assumption")
        if response.status_code == 204:
            return {"success": True, "org_id": org_id}
        if response.status_code == 404:
            return {"error": "Asumsi tidak ditemukan atau organisasi tidak ada", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}
