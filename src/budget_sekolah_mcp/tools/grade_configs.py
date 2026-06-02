"""
Tool MCP untuk konfigurasi grade satuan pendidikan (UNIT only).

Menyediakan tool untuk membaca, membuat/memperbarui, dan menghapus konfigurasi
grade (jumlah kelas dan label tiap kelas) untuk organisasi bertipe UNIT.
Konfigurasi ini menentukan berapa banyak slot kelas yang aktif (1–6) serta
label kustomnya (mis. "Kelas 1" diganti "Tingkat A"). Bila konfigurasi belum
diisi, sistem memakai default 6 grade dengan label "Kelas 1"–"Kelas 6".

Tools yang tersedia:
  get_grade_config    — Baca konfigurasi grade untuk satu UNIT
  upsert_grade_config — Set atau perbarui konfigurasi grade untuk satu UNIT
  delete_grade_config — Hapus konfigurasi grade (kembali ke default)

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool konfigurasi grade ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def get_grade_config(org_id: int) -> dict:
        """Baca konfigurasi grade untuk satu organisasi UNIT.

        Konfigurasi grade menentukan jumlah kelas aktif (1–6) dan label
        masing-masing kelas. Bila belum pernah disimpan, backend mengembalikan
        404 dan asumsi memakai default 6 grade ("Kelas 1"–"Kelas 6").

        Args:
            org_id: ID numerik organisasi UNIT.

        Returns:
            Dict berisi konfigurasi grade, termasuk kunci:
            - ``num_grades``: jumlah kelas aktif (1–6)
            - ``grade_1_label`` s/d ``grade_6_label``: label tiap kelas (null = default)
            - ``active_grades``: list slot aktif berisi ``slot`` dan ``label`` efektif
            Atau kunci ``error`` jika belum diisi atau bukan organisasi UNIT.

        Example:
            >>> result = await get_grade_config(org_id=3)
            >>> result["active_grades"][0]["label"]
            'Kelas 1'
        """
        response = await client.get(f"/organizations/{org_id}/grade-config")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {
                "error": "Konfigurasi grade belum diisi atau organisasi tidak ditemukan",
                "org_id": org_id,
            }
        if response.status_code == 422:
            return {
                "error": "Konfigurasi grade hanya berlaku untuk organisasi UNIT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def upsert_grade_config(
        org_id: int,
        num_grades: int = 6,
        grade_1_label: str | None = None,
        grade_2_label: str | None = None,
        grade_3_label: str | None = None,
        grade_4_label: str | None = None,
        grade_5_label: str | None = None,
        grade_6_label: str | None = None,
    ) -> dict:
        """Set atau perbarui konfigurasi grade untuk satu organisasi UNIT.

        Jika konfigurasi belum ada akan dibuat baru, jika sudah ada akan diperbarui.
        Label di luar rentang ``num_grades`` harus dibiarkan None — mis. jika
        ``num_grades=3`` maka ``grade_4_label`` s/d ``grade_6_label`` wajib None.
        Label None berarti memakai label default "Kelas N".

        Args:
            org_id: ID numerik organisasi UNIT.
            num_grades: Jumlah kelas aktif, harus 1–6 (default 6).
            grade_1_label: Label kustom kelas 1 (None = "Kelas 1").
            grade_2_label: Label kustom kelas 2 (None = "Kelas 2").
            grade_3_label: Label kustom kelas 3 (None = "Kelas 3").
            grade_4_label: Label kustom kelas 4 (None = "Kelas 4").
            grade_5_label: Label kustom kelas 5 (None = "Kelas 5").
            grade_6_label: Label kustom kelas 6 (None = "Kelas 6").

        Returns:
            Dict konfigurasi grade setelah disimpan (termasuk ``active_grades``),
            atau kunci ``error`` jika gagal.

        Example:
            >>> result = await upsert_grade_config(
            ...     org_id=3, num_grades=3,
            ...     grade_1_label="TK A", grade_2_label="TK B", grade_3_label="TK C"
            ... )
            >>> result["num_grades"]
            3
        """
        payload = {
            "num_grades": num_grades,
            "grade_1_label": grade_1_label,
            "grade_2_label": grade_2_label,
            "grade_3_label": grade_3_label,
            "grade_4_label": grade_4_label,
            "grade_5_label": grade_5_label,
            "grade_6_label": grade_6_label,
        }
        response = await client.put(f"/organizations/{org_id}/grade-config", json=payload)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        if response.status_code == 422:
            return {
                "error": (
                    "Konfigurasi grade hanya berlaku untuk UNIT, atau label "
                    "di luar num_grades tidak boleh diisi"
                ),
                "org_id": org_id,
                "detail": response.text,
            }
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_grade_config(org_id: int) -> dict:
        """Hapus konfigurasi grade untuk satu organisasi UNIT.

        Setelah dihapus, asumsi kembali ke default 6 grade dengan label
        "Kelas 1"–"Kelas 6".

        Args:
            org_id: ID numerik organisasi UNIT.

        Returns:
            Dict ``{"success": True, "org_id": org_id}`` jika berhasil,
            atau kunci ``error`` jika gagal.
        """
        response = await client.delete(f"/organizations/{org_id}/grade-config")
        if response.status_code == 204:
            return {"success": True, "org_id": org_id}
        if response.status_code == 404:
            return {
                "error": "Konfigurasi grade belum diisi atau organisasi tidak ada",
                "org_id": org_id,
            }
        if response.status_code == 422:
            return {
                "error": "Konfigurasi grade hanya berlaku untuk organisasi UNIT",
                "org_id": org_id,
            }
        return {"error": response.text, "status_code": response.status_code}
