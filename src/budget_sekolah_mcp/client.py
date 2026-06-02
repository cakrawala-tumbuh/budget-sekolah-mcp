"""
Async HTTP client wrapper untuk budget-backend-ypii.

BudgetApiClient membungkus httpx.AsyncClient dan menangani:
  - Autentikasi JWT otomatis (login saat startup, re-login pada 401)
  - Base URL dari konfigurasi
  - Timeout dari konfigurasi
  - Serialisasi/deserialisasi JSON

Semua tool MCP menggunakan satu instance client yang diinisialisasi
di server.py dan diteruskan via dependency injection sederhana.

Fungsi utama:
  BudgetApiClient.get     — HTTP GET
  BudgetApiClient.post    — HTTP POST
  BudgetApiClient.put     — HTTP PUT
  BudgetApiClient.delete  — HTTP DELETE
  BudgetApiClient.startup — login ke backend (dipanggil saat server start)
"""

import logging

import httpx

from . import auth
from .config import settings

logger = logging.getLogger(__name__)


class BudgetApiClient:
    """Async HTTP client dengan autentikasi JWT untuk budget-backend-ypii.

    Semua URL endpoint di-hard-code hanya di kelas ini — tidak di tools.
    Token JWT disimpan di modul auth.py (memori, tidak ke disk).

    Attributes:
        _client: Instance httpx.AsyncClient yang digunakan untuk semua request.
    """

    def __init__(self) -> None:
        """Inisialisasi client dengan base URL dan timeout dari konfigurasi."""
        self._client = httpx.AsyncClient(
            base_url=settings.budget_api_base_url,
            timeout=settings.http_timeout,
        )

    async def startup(self) -> None:
        """Login ke backend dan dapatkan JWT token.

        Harus dipanggil sekali sebelum melakukan request apapun.
        Biasanya dipanggil dari lifespan FastMCP di server.py.

        Raises:
            httpx.HTTPStatusError: Jika login gagal.
        """
        await auth.login(self._client)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        params: dict | None = None,
        data: dict | None = None,
        retry_on_401: bool = True,
    ) -> httpx.Response:
        """Kirim HTTP request dengan header autentikasi.

        Jika response 401, lakukan re-login otomatis dan coba sekali lagi.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: Path endpoint relatif terhadap base URL.
            json: Body request sebagai dict/list (dikodekan sebagai JSON).
            params: Query parameters.
            data: Form data (untuk OAuth2 login).
            retry_on_401: Jika True, re-login dan coba ulang saat dapat 401.

        Returns:
            httpx.Response dari server.

        Raises:
            httpx.HTTPStatusError: Jika request gagal dan tidak di-handle.
        """
        headers = auth.get_auth_header()
        response = await self._client.request(
            method,
            path,
            headers=headers,
            json=json,
            params=params,
            data=data,
        )

        if response.status_code == 401 and retry_on_401:
            logger.warning("Mendapat 401 pada %s %s — melakukan re-login", method, path)
            headers = await auth.handle_401(self._client)
            response = await self._client.request(
                method,
                path,
                headers=headers,
                json=json,
                params=params,
                data=data,
            )

        return response

    async def get(self, path: str, *, params: dict | None = None) -> httpx.Response:
        """Kirim HTTP GET request.

        Args:
            path: Path endpoint (contoh: "/organizations").
            params: Query parameters opsional.

        Returns:
            httpx.Response dari server.
        """
        return await self._request("GET", path, params=params)

    async def post(self, path: str, *, json: dict | list | None = None) -> httpx.Response:
        """Kirim HTTP POST request dengan body JSON.

        Args:
            path: Path endpoint (contoh: "/organizations").
            json: Body request sebagai dict atau list.

        Returns:
            httpx.Response dari server.
        """
        return await self._request("POST", path, json=json)

    async def put(self, path: str, *, json: dict | None = None) -> httpx.Response:
        """Kirim HTTP PUT request dengan body JSON.

        Args:
            path: Path endpoint.
            json: Body request sebagai dict.

        Returns:
            httpx.Response dari server.
        """
        return await self._request("PUT", path, json=json)

    async def patch(self, path: str, *, json: dict | None = None) -> httpx.Response:
        """Kirim HTTP PATCH request dengan body JSON (partial update).

        Args:
            path: Path endpoint.
            json: Body request sebagai dict (hanya field yang diubah).

        Returns:
            httpx.Response dari server.
        """
        return await self._request("PATCH", path, json=json)

    async def delete(self, path: str) -> httpx.Response:
        """Kirim HTTP DELETE request.

        Args:
            path: Path endpoint yang akan dihapus.

        Returns:
            httpx.Response dari server.
        """
        return await self._request("DELETE", path)

    async def aclose(self) -> None:
        """Tutup koneksi HTTP client.

        Dipanggil saat server shutdown untuk melepas resource.
        """
        await self._client.aclose()
