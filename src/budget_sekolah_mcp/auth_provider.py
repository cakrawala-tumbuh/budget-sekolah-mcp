"""
Custom auth providers untuk budget-sekolah-mcp.

Menyediakan dua komponen autentikasi:

  GithubUsernameFilteredProvider  — subclass GitHubProvider yang membatasi
      akses hanya untuk GitHub username yang tercantum di GITHUB_ALLOWED_USERNAMES.
      Pemeriksaan dilakukan satu kali saat token pertama kali ditukar (bukan
      di setiap request), sehingga tidak mempengaruhi performa.

  BearerApiKeyVerifier  — TokenVerifier sederhana yang memvalidasi static
      Bearer token. Digunakan untuk akses via VS Code / tools non-Claude.ai
      (tidak perlu OAuth flow).

Cara pemakaian di server.py:
  from .auth_provider import GithubUsernameFilteredProvider, BearerApiKeyVerifier
  from fastmcp.server.auth import MultiAuth

  provider = GithubUsernameFilteredProvider(
      client_id=settings.github_client_id,
      client_secret=settings.github_client_secret,
      base_url=settings.mcp_base_url,
      allowed_usernames=settings.github_allowed_usernames,
  )
  auth = MultiAuth(
      server=provider,
      verifiers=[BearerApiKeyVerifier(api_key=settings.mcp_api_key)],
  )
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.auth.providers.github import GitHubProvider
from mcp.server.auth.provider import TokenError

logger = logging.getLogger(__name__)


class GithubUsernameFilteredProvider(GitHubProvider):
    """GitHubProvider yang membatasi akses berdasarkan GitHub username.

    Ketika pengguna berhasil login via GitHub, provider ini memanggil
    ``https://api.github.com/user`` untuk mendapatkan username. Jika username
    tidak ada dalam daftar yang diizinkan, token FastMCP tidak akan diterbitkan
    dan pengguna mendapat respons error ``access_denied``.

    Pemeriksaan hanya terjadi satu kali saat pertukaran authorization code —
    tidak di setiap request berikutnya.

    Args:
        allowed_usernames: Daftar GitHub username yang diizinkan (case-insensitive).
            Jika kosong, semua pengguna GitHub yang berhasil login dapat mengakses.
        **kwargs: Diteruskan ke ``GitHubProvider.__init__``.

    Example:
        >>> provider = GithubUsernameFilteredProvider(
        ...     client_id="Ov23li...",
        ...     client_secret="abc123...",
        ...     base_url="https://mcp.example.com",
        ...     allowed_usernames=["andhit-r"],
        ... )
    """

    def __init__(self, *, allowed_usernames: list[str], **kwargs: Any) -> None:
        """Inisialisasi provider dengan daftar username yang diizinkan.

        Args:
            allowed_usernames: Daftar GitHub username yang boleh login.
                Kosong berarti semua username diizinkan.
            **kwargs: Argumen untuk GitHubProvider (client_id, client_secret,
                base_url, require_authorization_consent, dsb.).
        """
        super().__init__(**kwargs)
        self._allowed_usernames: frozenset[str] = frozenset(
            u.lower().strip() for u in allowed_usernames if u.strip()
        )

    async def _extract_upstream_claims(
        self, idp_tokens: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Validasi GitHub username dan kembalikan claims untuk disematkan di JWT.

        Memanggil GitHub API untuk mendapatkan identitas pengguna dari
        access_token yang diterima. Jika username tidak dalam daftar yang
        diizinkan, raise TokenError sehingga token tidak diterbitkan.

        Args:
            idp_tokens: Response token dari GitHub OAuth, berisi ``access_token``,
                ``token_type``, dan ``scope``.

        Returns:
            Dict berisi ``login`` (GitHub username) dan ``github_id`` (user ID
            numerik GitHub) untuk disematkan sebagai klaim di FastMCP JWT.

        Raises:
            TokenError: Jika GitHub API tidak dapat dihubungi, token tidak valid,
                atau username tidak ada dalam daftar yang diizinkan.
        """
        access_token = idp_tokens.get("access_token", "")
        if not access_token:
            raise TokenError("access_denied", "Upstream access token tidak tersedia")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                        "User-Agent": "budget-sekolah-mcp",
                    },
                )
        except httpx.RequestError as exc:
            logger.warning("Gagal menghubungi GitHub API: %s", exc)
            raise TokenError(
                "server_error", "Tidak dapat memverifikasi identitas GitHub"
            ) from exc

        if response.status_code != 200:
            logger.warning(
                "GitHub API menolak token (status=%d): %s",
                response.status_code,
                response.text[:200],
            )
            raise TokenError("access_denied", "Token GitHub tidak valid")

        user_data = response.json()
        login: str = user_data.get("login", "").lower().strip()

        if not login:
            raise TokenError("access_denied", "Tidak dapat mengambil username GitHub")

        # Periksa whitelist username (jika kosong = semua diizinkan)
        if self._allowed_usernames and login not in self._allowed_usernames:
            logger.warning(
                "Akses ditolak untuk GitHub user '%s' — bukan dalam daftar yang diizinkan",
                login,
            )
            raise TokenError(
                "access_denied",
                f"GitHub user '{login}' tidak diizinkan mengakses server ini",
            )

        logger.info("GitHub user '%s' berhasil diautentikasi", login)
        return {
            "login": login,
            "github_id": user_data.get("id"),
            "name": user_data.get("name"),
        }


class BearerApiKeyVerifier(TokenVerifier):
    """TokenVerifier yang memvalidasi static Bearer token (API key).

    Digunakan untuk akses dari VS Code, tools CLI, atau sistem otomatis
    yang tidak mendukung OAuth flow. Token yang valid adalah nilai persis
    dari ``MCP_API_KEY``.

    Token dapat dikirim via header ``Authorization: Bearer <api_key>``.

    Args:
        api_key: API key yang valid. Tidak boleh kosong.

    Example:
        >>> verifier = BearerApiKeyVerifier(api_key="abc123...")
        >>> token = await verifier.verify_token("abc123...")
        >>> token.client_id
        'api-key-client'
    """

    def __init__(self, api_key: str) -> None:
        """Inisialisasi verifier dengan API key statis.

        Args:
            api_key: API key yang diterima sebagai Bearer token yang valid.

        Raises:
            ValueError: Jika api_key kosong atau hanya whitespace.
        """
        if not api_key or not api_key.strip():
            raise ValueError("api_key tidak boleh kosong")
        super().__init__()
        self._api_key = api_key

    async def verify_token(self, token: str) -> AccessToken | None:
        """Validasi Bearer token terhadap API key yang dikonfigurasi.

        Args:
            token: Bearer token dari header Authorization.

        Returns:
            AccessToken jika token cocok dengan api_key, atau None jika tidak cocok.

        Example:
            >>> result = await verifier.verify_token("wrong-key")
            >>> result is None
            True
        """
        if token == self._api_key:
            return AccessToken(
                token=token,
                client_id="api-key-client",
                scopes=[],
            )
        return None
