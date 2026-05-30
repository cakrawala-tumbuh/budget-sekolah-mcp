"""
Custom auth providers untuk budget-sekolah-mcp.

Menyediakan dua komponen autentikasi:

  AuthentikProvider  — subclass OAuthProxy yang menggunakan Authentik sebagai
      identity provider (IdP). Mendukung OAuth 2.0 Authorization Code Flow
      dengan PKCE. Token diverifikasi via JWKS endpoint Authentik.
      Opsional: batasi akses hanya untuk username tertentu via
      AUTHENTIK_ALLOWED_USERNAMES.

  BearerApiKeyVerifier  — TokenVerifier sederhana yang memvalidasi static
      Bearer token. Digunakan untuk akses via VS Code / tools non-Claude.ai
      (tidak perlu OAuth flow).

Cara pemakaian di server.py:
  from .auth_provider import AuthentikProvider, BearerApiKeyVerifier
  from fastmcp.server.auth import MultiAuth

  provider = AuthentikProvider(
      authentik_base_url=settings.authentik_base_url,
      application_slug=settings.authentik_app_slug,
      client_id=settings.authentik_client_id,
      client_secret=settings.authentik_client_secret,
      base_url=settings.mcp_base_url,
      allowed_usernames=settings.authentik_allowed_usernames,
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
from fastmcp.server.auth.oauth_proxy.proxy import OAuthProxy
from fastmcp.server.auth.providers.jwt import JWTVerifier
from mcp.server.auth.provider import TokenError

logger = logging.getLogger(__name__)


class AuthentikProvider(OAuthProxy):
    """OAuthProxy yang menggunakan Authentik sebagai identity provider.

    Authentik bertindak sebagai OAuth 2.0 / OIDC server. MCP server ini
    berperan sebagai proxy — mengarahkan login ke Authentik, menerima token,
    memverifikasinya via JWKS, dan menerbitkan FastMCP JWT kepada MCP client
    (Claude.ai, VS Code, dsb.).

    URL endpoint Authentik dibangun otomatis dari ``authentik_base_url`` dan
    ``application_slug``. Contoh untuk Authentik di
    ``https://auth.cantum-ypii.com`` dengan slug ``budget-mcp``:
      - Authorize : ``/application/o/budget-mcp/authorize/``
      - Token     : ``/application/o/budget-mcp/token/``
      - JWKS      : ``/application/o/budget-mcp/jwks/``
      - Userinfo  : ``/application/o/userinfo/``

    Args:
        authentik_base_url: URL dasar Authentik, contoh
            ``https://auth.cantum-ypii.com``. Tanpa trailing slash.
        application_slug: Slug OAuth2/OIDC Provider di Authentik, contoh
            ``budget-mcp``.
        client_id: Client ID dari Authentik OAuth2 Provider.
        client_secret: Client Secret dari Authentik OAuth2 Provider.
        base_url: URL publik MCP server ini, contoh
            ``https://mcp.budget-26.cantum-ypii.com``.
        allowed_usernames: Daftar ``preferred_username`` Authentik yang
            diizinkan (case-insensitive). Kosong = semua user Authentik
            yang berhasil login dapat mengakses.
        **kwargs: Diteruskan ke ``OAuthProxy.__init__`` (misal
            ``require_authorization_consent``, ``jwt_signing_key``, dsb.).

    Example:
        >>> provider = AuthentikProvider(
        ...     authentik_base_url="https://auth.cantum-ypii.com",
        ...     application_slug="budget-mcp",
        ...     client_id="abc123",
        ...     client_secret="secret",
        ...     base_url="https://mcp.budget-26.cantum-ypii.com",
        ...     allowed_usernames=["andhit-r"],
        ... )
    """

    def __init__(
        self,
        *,
        authentik_base_url: str,
        application_slug: str,
        client_id: str,
        client_secret: str,
        base_url: str,
        allowed_usernames: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Inisialisasi AuthentikProvider dengan konfigurasi Authentik.

        Args:
            authentik_base_url: URL dasar Authentik (tanpa trailing slash).
            application_slug: Slug OAuth2 Provider di Authentik.
            client_id: Client ID dari Authentik OAuth2 Provider.
            client_secret: Client Secret dari Authentik OAuth2 Provider.
            base_url: URL publik MCP server.
            allowed_usernames: Daftar username Authentik yang diizinkan.
                None atau kosong = semua user diizinkan.
            **kwargs: Argumen tambahan untuk OAuthProxy.
        """
        base = authentik_base_url.rstrip("/")
        slug = application_slug.strip("/")

        authorize_url = f"{base}/application/o/{slug}/authorize/"
        token_url = f"{base}/application/o/{slug}/token/"
        jwks_url = f"{base}/application/o/{slug}/jwks/"
        revoke_url = f"{base}/application/o/{slug}/end-session/"
        issuer_url = f"{base}/application/o/{slug}/"
        self._userinfo_url = f"{base}/application/o/userinfo/"

        token_verifier = JWTVerifier(
            jwks_uri=jwks_url,
            issuer=issuer_url,
        )

        super().__init__(
            upstream_authorization_endpoint=authorize_url,
            upstream_token_endpoint=token_url,
            upstream_client_id=client_id,
            upstream_client_secret=client_secret,
            upstream_revocation_endpoint=revoke_url,
            token_verifier=token_verifier,
            base_url=base_url,
            valid_scopes=["openid", "profile", "email"],
            **kwargs,
        )

        self._allowed_usernames: frozenset[str] = frozenset(
            u.lower().strip() for u in (allowed_usernames or []) if u.strip()
        )
        logger.debug(
            "AuthentikProvider diinisialisasi — issuer: %s | allowed: %s",
            issuer_url,
            list(self._allowed_usernames) or "(semua diizinkan)",
        )

    async def _extract_upstream_claims(self, idp_tokens: dict[str, Any]) -> dict[str, Any] | None:
        """Ambil klaim pengguna dari Authentik dan validasi akses.

        Memanggil userinfo endpoint Authentik untuk mendapatkan identitas
        pengguna dari access_token yang diterima. Jika ``allowed_usernames``
        dikonfigurasi dan ``preferred_username`` tidak ada dalam daftar,
        TokenError akan di-raise sehingga token FastMCP tidak diterbitkan.

        Pemeriksaan hanya terjadi satu kali saat pertukaran authorization
        code — tidak di setiap request berikutnya.

        Args:
            idp_tokens: Response token dari Authentik, berisi ``access_token``,
                opsional ``id_token``, ``refresh_token``, dsb.

        Returns:
            Dict klaim untuk disematkan di FastMCP JWT, berisi:
            ``username``, ``email``, ``name``, ``sub``, ``groups``.

        Raises:
            TokenError: Jika access_token tidak ada, userinfo endpoint tidak
                dapat dihubungi, atau username tidak ada dalam daftar yang
                diizinkan.
        """
        access_token = idp_tokens.get("access_token", "")
        if not access_token:
            raise TokenError("access_denied", "Upstream access token tidak tersedia")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self._userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.RequestError as exc:
            logger.warning("Gagal menghubungi Authentik userinfo: %s", exc)
            raise TokenError(
                "server_error", "Tidak dapat memverifikasi identitas dari Authentik"
            ) from exc

        if response.status_code != 200:
            logger.warning(
                "Authentik userinfo menolak token (status=%d): %s",
                response.status_code,
                response.text[:200],
            )
            raise TokenError("access_denied", "Token Authentik tidak valid atau kedaluwarsa")

        userinfo = response.json()
        username: str = (
            (userinfo.get("preferred_username") or userinfo.get("sub", "")).lower().strip()
        )

        if not username:
            raise TokenError("access_denied", "Tidak dapat mengambil username dari Authentik")

        if self._allowed_usernames and username not in self._allowed_usernames:
            logger.warning(
                "Akses ditolak untuk user Authentik '%s' — bukan dalam daftar yang diizinkan",
                username,
            )
            raise TokenError(
                "access_denied",
                f"User '{username}' tidak diizinkan mengakses server ini",
            )

        logger.info("User Authentik '%s' berhasil diautentikasi", username)
        return {
            "username": username,
            "email": userinfo.get("email"),
            "name": userinfo.get("name"),
            "sub": userinfo.get("sub"),
            "groups": userinfo.get("groups", []),
        }


class BearerApiKeyVerifier(TokenVerifier):
    """TokenVerifier yang memvalidasi static Bearer token (API key).

    Digunakan untuk akses dari VS Code, tools CLI, atau sistem otomatis
    yang tidak mendukung OAuth flow. Token yang valid adalah nilai persis
    dari ``MCP_API_KEY``.

    Setiap request yang membawa header ``Authorization: Bearer <token>``
    akan dicocokkan dengan API key yang dikonfigurasi. Jika cocok,
    AccessToken dengan ``client_id="api-key-client"`` dikembalikan.

    Args:
        api_key: API key statis. Tidak boleh kosong atau hanya spasi.

    Raises:
        ValueError: Jika ``api_key`` kosong atau hanya berisi spasi.

    Example:
        >>> verifier = BearerApiKeyVerifier(api_key="secret-key-abc")
        >>> result = await verifier.verify_token("secret-key-abc")
        >>> result.client_id
        'api-key-client'
    """

    def __init__(self, *, api_key: str) -> None:
        """Inisialisasi verifier dengan API key statis.

        Args:
            api_key: API key yang akan dicocokkan. Wajib non-kosong.

        Raises:
            ValueError: Jika ``api_key`` kosong atau hanya spasi.
        """
        if not api_key or not api_key.strip():
            raise ValueError("api_key tidak boleh kosong")
        self._api_key = api_key

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verifikasi token dengan membandingkan ke API key yang dikonfigurasi.

        Args:
            token: Bearer token dari header Authorization request.

        Returns:
            AccessToken jika token cocok dengan API key, None jika tidak cocok.
        """
        if token == self._api_key:
            return AccessToken(
                token=token,
                client_id="api-key-client",
                scopes=[],
            )
        return None
