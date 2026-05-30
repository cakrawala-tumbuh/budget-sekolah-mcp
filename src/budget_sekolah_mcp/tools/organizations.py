"""
Tool MCP untuk manajemen organisasi (UNIT, CABANG, PUSAT).

Menyediakan tool-tool CRUD untuk entitas Organization di budget-backend-ypii.
Operasi create, update, dan delete membutuhkan akses admin.

Tools yang tersedia:
  list_organizations   — Daftar semua organisasi
  get_organization     — Detail satu organisasi beserta anak langsungnya
  create_organization  — Buat organisasi baru (admin only)
  update_organization  — Update nama/kota/parent organisasi (admin only)
  delete_organization  — Hapus organisasi (admin only)

Dependensi:
  client.BudgetApiClient — HTTP client ke backend API
"""

from fastmcp import FastMCP

from ..client import BudgetApiClient


def register(mcp: FastMCP, client: BudgetApiClient) -> None:
    """Daftarkan semua tool organisasi ke instance FastMCP.

    Args:
        mcp: Instance FastMCP tempat tool didaftarkan.
        client: Instance BudgetApiClient untuk komunikasi ke backend.
    """

    @mcp.tool()
    async def list_organizations(skip: int = 0, limit: int = 200) -> dict:
        """Ambil daftar semua organisasi yang terdaftar di sistem.

        Mengembalikan UNIT, CABANG, dan PUSAT secara bersamaan.
        Gunakan parameter skip/limit untuk pagination jika jumlah organisasi banyak.

        Args:
            skip: Jumlah baris yang dilewati (default: 0).
            limit: Jumlah maksimum baris yang dikembalikan (default: 200).

        Returns:
            Dict dengan kunci ``items`` berisi list organisasi, atau
            kunci ``error`` jika request gagal.

        Example:
            >>> result = await list_organizations()
            >>> result["items"][0]["code"]
            'PUSAT'
        """
        response = await client.get("/organizations", params={"skip": skip, "limit": limit})
        if response.status_code == 200:
            return {"items": response.json()}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def get_organization(org_id: int) -> dict:
        """Ambil detail satu organisasi beserta daftar anak langsungnya.

        Args:
            org_id: ID numerik organisasi yang ingin dilihat.

        Returns:
            Dict data organisasi termasuk kunci ``children`` (list anak langsung),
            atau kunci ``error`` jika tidak ditemukan.

        Example:
            >>> result = await get_organization(org_id=1)
            >>> result["org_type"]
            'PUSAT'
        """
        response = await client.get(f"/organizations/{org_id}")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def create_organization(
        code: str,
        name: str,
        org_type: str,
        city: str | None = None,
        parent_id: int | None = None,
    ) -> dict:
        """Buat organisasi baru di sistem (membutuhkan akses admin).

        Secara otomatis membuat user login untuk organisasi ini.
        Password awal dikembalikan sekali dalam response — simpan baik-baik.

        Args:
            code: Kode unik organisasi, akan dinormalisasi ke uppercase.
                  Contoh: "SD-MBL", "CABANG-BDG".
            name: Nama lengkap organisasi.
            org_type: Tipe organisasi — "UNIT", "CABANG", atau "PUSAT".
            city: Kota tempat organisasi berada (opsional).
            parent_id: ID organisasi induk (opsional; UNIT punya CABANG sebagai parent).

        Returns:
            Dict data organisasi yang dibuat, termasuk kunci ``generated_password``
            yang hanya muncul sekali. Atau kunci ``error`` jika gagal.

        Example:
            >>> result = await create_organization(
            ...     code="SD-MBL", name="SD Maria Bintang Laut",
            ...     org_type="UNIT", city="Bandung", parent_id=2
            ... )
            >>> result["generated_password"]
            'xK9mP...'
        """
        payload: dict = {"code": code, "name": name, "org_type": org_type}
        if city is not None:
            payload["city"] = city
        if parent_id is not None:
            payload["parent_id"] = parent_id

        response = await client.post("/organizations", json=payload)
        if response.status_code == 201:
            return response.json()
        if response.status_code == 409:
            return {"error": f"Kode organisasi '{code}' sudah digunakan"}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def update_organization(
        org_id: int,
        name: str | None = None,
        city: str | None = None,
        parent_id: int | None = None,
    ) -> dict:
        """Update data organisasi yang sudah ada (membutuhkan akses admin).

        Hanya field yang diisi yang akan diperbarui. Kode organisasi tidak
        dapat diubah setelah dibuat.

        Args:
            org_id: ID numerik organisasi yang akan diupdate.
            name: Nama baru organisasi (opsional).
            city: Kota baru (opsional).
            parent_id: ID parent baru (opsional).

        Returns:
            Dict data organisasi setelah diupdate, atau kunci ``error`` jika gagal.
        """
        payload: dict = {}
        if name is not None:
            payload["name"] = name
        if city is not None:
            payload["city"] = city
        if parent_id is not None:
            payload["parent_id"] = parent_id

        response = await client.put(f"/organizations/{org_id}", json=payload)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}

    @mcp.tool()
    async def delete_organization(org_id: int) -> dict:
        """Hapus organisasi dari sistem (membutuhkan akses admin).

        Peringatan: operasi ini tidak dapat dibatalkan. Pastikan tidak ada
        data anggaran yang masih aktif sebelum menghapus.

        Args:
            org_id: ID numerik organisasi yang akan dihapus.

        Returns:
            Dict ``{"success": True, "org_id": org_id}`` jika berhasil,
            atau kunci ``error`` jika gagal.
        """
        response = await client.delete(f"/organizations/{org_id}")
        if response.status_code == 204:
            return {"success": True, "org_id": org_id}
        if response.status_code == 404:
            return {"error": "Organization not found", "org_id": org_id}
        return {"error": response.text, "status_code": response.status_code}
