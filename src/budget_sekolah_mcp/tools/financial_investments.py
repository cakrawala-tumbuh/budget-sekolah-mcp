"""
Tool MCP untuk investasi keuangan (baca-saja).

Investasi keuangan adalah penempatan dana CABANG/PUSAT pada instrumen seperti
saham, reksa dana, obligasi, atau deposito. Entitas ini BERBEDA dari investasi
aset tetap (modul ``investments``).

Tools yang tersedia:
  list_financial_investments — Daftar investasi keuangan untuk satu organisasi

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan tool investasi keuangan ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_financial_investments(org_id: int) -> dict:
        """Ambil daftar investasi KEUANGAN (deposito, saham, reksa dana, dsb.) satu organisasi.

        Khusus CABANG/PUSAT. Jangan tertukar dengan ``list_investments`` yang
        membaca investasi aset tetap baru.

        Args:
            org_id: ID numerik organisasi.

        Returns:
            Dict dengan kunci ``items`` berisi list investasi keuangan apa adanya
            dari backend (``id``, ``organization_id``, ``instrument_type`` ∈
            SAHAM/REKSA_DANA/OBLIGASI/DEPOSITO/LAINNYA, ``name``, ``amount``,
            ``notes``, ``created_at``, ``updated_at``). Atau kunci ``error``
            (disertai ``org_id`` untuk 404, atau ``status_code`` untuk status lain
            seperti 403 organisasi di luar naungan) jika gagal.
        """
        response = await client.get(f"/organizations/{org_id}/financial-investments")
        if response.status_code == 200:
            return {"items": response.json()}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}
