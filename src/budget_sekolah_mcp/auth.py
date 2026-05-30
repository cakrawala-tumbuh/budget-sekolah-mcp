"""
Manajemen autentikasi JWT ke budget-backend-ypii.

Token JWT disimpan di memori (tidak pernah ke disk). Jika response HTTP
mengembalikan 401, modul ini melakukan re-login otomatis dan menyediakan
header Authorization yang diperbarui.

Fungsi utama:
  get_auth_header  — kembalikan dict header Authorization: Bearer <token>
  login            — autentikasi ke backend dan simpan token
  handle_401       — re-login ketika token kadaluarsa, kembalikan header baru
"""

import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_access_token: str | None = None


async def login(client: httpx.AsyncClient) -> str:
    """Login ke backend API dan simpan JWT token di memori.

    Mengirim POST /auth/login dengan form data OAuth2. Token yang diterima
    disimpan di variabel modul-level (tidak di disk).

    Args:
        client: Instance httpx.AsyncClient yang sudah dikonfigurasi dengan base_url.

    Returns:
        JWT access token sebagai string.

    Raises:
        httpx.HTTPStatusError: Jika login gagal (kredensial salah, server down, dsb.).
    """
    global _access_token

    logger.info("Melakukan login ke backend API sebagai '%s'", settings.budget_api_username)
    response = await client.post(
        "/auth/login",
        data={
            "username": settings.budget_api_username,
            "password": settings.budget_api_password,
        },
    )
    response.raise_for_status()
    _access_token = response.json()["access_token"]
    logger.info("Login berhasil — token disimpan di memori")
    return _access_token


def get_auth_header() -> dict[str, str]:
    """Kembalikan header Authorization yang berisi JWT token saat ini.

    Returns:
        Dict {"Authorization": "Bearer <token>"}, atau dict kosong jika
        belum pernah login.
    """
    if _access_token is None:
        return {}
    return {"Authorization": f"Bearer {_access_token}"}


async def handle_401(client: httpx.AsyncClient) -> dict[str, str]:
    """Re-login setelah menerima respons 401 Unauthorized.

    Dipanggil oleh BudgetApiClient ketika suatu request mendapat response 401.
    Melakukan login ulang dan mengembalikan header Authorization yang diperbarui.

    Args:
        client: Instance httpx.AsyncClient untuk melakukan request login ulang.

    Returns:
        Dict header Authorization: Bearer <token_baru>.

    Raises:
        httpx.HTTPStatusError: Jika re-login juga gagal.
    """
    logger.warning("Token expired atau tidak valid — mencoba re-login")
    await login(client)
    return get_auth_header()
