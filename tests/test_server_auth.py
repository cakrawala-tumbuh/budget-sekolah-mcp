"""
Unit test untuk mekanisme autentikasi server.

Menguji komponen-komponen auth yang ada:

  - AuthentikProvider: filter username Authentik via OIDC userinfo endpoint
  - BearerApiKeyVerifier: validasi static API key
  - Logika pemilihan auth di server.py berdasarkan konfigurasi
  - asgi.py menghasilkan ASGI app yang benar

Catatan: Test ini tidak membutuhkan koneksi Authentik nyata —
semua HTTP call ke userinfo endpoint di-mock via respx.
"""

import httpx
import pytest
from fastmcp.server.auth import TokenVerifier
from fastmcp.server.auth.oauth_proxy.proxy import OAuthProxy
from mcp.server.auth.provider import TokenError

from budget_sekolah_mcp.auth_provider import AuthentikProvider, BearerApiKeyVerifier
from budget_sekolah_mcp.middleware import ApiKeyMiddleware

# URL mock yang dipakai di semua test Authentik
_AUTHENTIK_BASE = "https://auth.example.com"
_APP_SLUG = "budget-mcp"
_USERINFO_URL = f"{_AUTHENTIK_BASE}/application/o/userinfo/"


class TestBearerApiKeyVerifier:
    """Test BearerApiKeyVerifier — validasi static API key."""

    def test_inisialisasi_dengan_api_key_valid(self):
        """BearerApiKeyVerifier harus bisa dibuat dengan API key yang valid."""
        verifier = BearerApiKeyVerifier(api_key="secret-key-123")
        assert verifier is not None

    def test_inisialisasi_dengan_api_key_kosong_raise_valueerror(self):
        """BearerApiKeyVerifier harus raise ValueError jika api_key kosong."""
        with pytest.raises(ValueError, match="api_key"):
            BearerApiKeyVerifier(api_key="")

    def test_inisialisasi_dengan_whitespace_raise_valueerror(self):
        """BearerApiKeyVerifier harus raise ValueError jika api_key hanya spasi."""
        with pytest.raises(ValueError, match="api_key"):
            BearerApiKeyVerifier(api_key="   ")

    @pytest.mark.asyncio
    async def test_verify_token_cocok_kembalikan_access_token(self):
        """verify_token harus mengembalikan AccessToken jika token cocok."""
        verifier = BearerApiKeyVerifier(api_key="my-secret-key")
        result = await verifier.verify_token("my-secret-key")

        assert result is not None
        assert result.client_id == "api-key-client"
        assert result.token == "my-secret-key"

    @pytest.mark.asyncio
    async def test_verify_token_salah_kembalikan_none(self):
        """verify_token harus mengembalikan None jika token tidak cocok."""
        verifier = BearerApiKeyVerifier(api_key="correct-key")
        result = await verifier.verify_token("wrong-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_kosong_kembalikan_none(self):
        """verify_token harus mengembalikan None untuk token kosong."""
        verifier = BearerApiKeyVerifier(api_key="correct-key")
        result = await verifier.verify_token("")

        assert result is None


def _make_provider(**kwargs) -> AuthentikProvider:
    """Buat AuthentikProvider dengan konfigurasi default untuk test."""
    defaults = {
        "authentik_base_url": _AUTHENTIK_BASE,
        "application_slug": _APP_SLUG,
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "base_url": "https://mcp.example.com",
        "allowed_usernames": [],
    }
    defaults.update(kwargs)
    return AuthentikProvider(**defaults)


class TestAuthentikProvider:
    """Test AuthentikProvider — filter username Authentik via userinfo endpoint."""

    def test_inisialisasi_dengan_satu_username(self):
        """Provider harus bisa dibuat dengan satu username yang diizinkan."""
        provider = _make_provider(allowed_usernames=["andhit-r"])
        assert provider is not None
        assert "andhit-r" in provider._allowed_usernames

    def test_inisialisasi_username_dinormalisasi_lowercase(self):
        """Username harus disimpan dalam lowercase."""
        provider = _make_provider(allowed_usernames=["AndhiT-R", "UserDua"])
        assert "andhit-r" in provider._allowed_usernames
        assert "userdua" in provider._allowed_usernames
        assert "AndhiT-R" not in provider._allowed_usernames

    def test_inisialisasi_tanpa_whitelist_diizinkan(self):
        """Provider harus bisa dibuat tanpa daftar username (semua diizinkan)."""
        provider = _make_provider(allowed_usernames=[])
        assert len(provider._allowed_usernames) == 0

    def test_inisialisasi_whitelist_none_diizinkan(self):
        """Provider harus bisa dibuat dengan allowed_usernames=None."""
        provider = _make_provider(allowed_usernames=None)
        assert len(provider._allowed_usernames) == 0

    def test_inisialisasi_adalah_subclass_oauthproxy(self):
        """AuthentikProvider harus merupakan subclass OAuthProxy."""
        provider = _make_provider()
        assert isinstance(provider, OAuthProxy)

    def test_userinfo_url_dibangun_dengan_benar(self):
        """URL userinfo Authentik harus dibangun dari authentik_base_url."""
        provider = _make_provider()
        assert provider._userinfo_url == _USERINFO_URL

    def test_trailing_slash_pada_base_url_dinormalisasi(self):
        """Trailing slash pada authentik_base_url harus diabaikan."""
        provider = _make_provider(authentik_base_url=f"{_AUTHENTIK_BASE}/")
        assert provider._userinfo_url == _USERINFO_URL

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_username_diizinkan(self, respx_mock):
        """_extract_upstream_claims harus mengembalikan claims jika username diizinkan."""
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "sub": "abc-123",
                    "preferred_username": "andhit-r",
                    "name": "Andhit",
                    "email": "andhit@example.com",
                    "groups": ["admin"],
                },
            )
        )

        provider = _make_provider(allowed_usernames=["andhit-r"])
        claims = await provider._extract_upstream_claims({"access_token": "authentik-access-token"})

        assert claims is not None
        assert claims["username"] == "andhit-r"
        assert claims["email"] == "andhit@example.com"
        assert claims["sub"] == "abc-123"
        assert "admin" in claims["groups"]

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_username_tidak_diizinkan(self, respx_mock):
        """_extract_upstream_claims harus raise TokenError jika username tidak diizinkan."""
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "sub": "xyz-999",
                    "preferred_username": "orang-lain",
                    "name": "Orang Lain",
                },
            )
        )

        provider = _make_provider(allowed_usernames=["andhit-r"])
        with pytest.raises(TokenError) as exc_info:
            await provider._extract_upstream_claims({"access_token": "authentik-access-token"})

        assert exc_info.value.error == "access_denied"
        assert "orang-lain" in exc_info.value.error_description

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_tanpa_whitelist_semua_diizinkan(self, respx_mock):
        """Jika allowed_usernames kosong, semua user Authentik harus diizinkan."""
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "sub": "abc-777",
                    "preferred_username": "siapapun",
                    "name": "Siapapun",
                },
            )
        )

        provider = _make_provider(allowed_usernames=[])
        claims = await provider._extract_upstream_claims({"access_token": "authentik-access-token"})

        assert claims is not None
        assert claims["username"] == "siapapun"

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_authentik_api_error(self, respx_mock):
        """_extract_upstream_claims harus raise TokenError jika Authentik userinfo error."""
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(401, json={"detail": "Token expired"})
        )

        provider = _make_provider(allowed_usernames=["andhit-r"])
        with pytest.raises(TokenError) as exc_info:
            await provider._extract_upstream_claims({"access_token": "expired-token"})

        assert exc_info.value.error == "access_denied"

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_tanpa_access_token(self):
        """_extract_upstream_claims harus raise TokenError jika access_token tidak ada."""
        provider = _make_provider(allowed_usernames=["andhit-r"])
        with pytest.raises(TokenError) as exc_info:
            await provider._extract_upstream_claims({})

        assert exc_info.value.error == "access_denied"

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_gunakan_sub_jika_preferred_username_kosong(
        self, respx_mock
    ):
        """Jika preferred_username tidak ada, gunakan sub sebagai username."""
        respx_mock.get(_USERINFO_URL).mock(
            return_value=httpx.Response(
                200,
                json={"sub": "user-sub-only"},
            )
        )

        provider = _make_provider(allowed_usernames=[])
        claims = await provider._extract_upstream_claims({"access_token": "authentik-access-token"})

        assert claims is not None
        assert claims["username"] == "user-sub-only"


class TestServerAuthMode:
    """Test pemilihan auth mode di server.py berdasarkan konfigurasi."""

    def test_auth_none_di_lingkungan_test(self):
        """Di lingkungan test (tanpa Authentik env vars), _auth harus None."""
        import budget_sekolah_mcp.server as server_mod

        assert server_mod._auth is None

    def test_bearer_verifier_adalah_token_verifier(self):
        """BearerApiKeyVerifier harus merupakan subclass dari TokenVerifier."""
        verifier = BearerApiKeyVerifier(api_key="test")
        assert isinstance(verifier, TokenVerifier)

    def test_authentik_provider_adalah_subclass_oauthproxy(self):
        """AuthentikProvider harus merupakan subclass OAuthProxy."""
        provider = _make_provider()
        assert isinstance(provider, OAuthProxy)


class TestAsgiApp:
    """Test bahwa asgi.py menghasilkan ASGI app yang valid."""

    def test_asgi_app_terinisialisasi(self):
        """asgi.app harus ada dan merupakan callable ASGI."""
        import budget_sekolah_mcp.asgi as asgi_mod

        assert asgi_mod.app is not None
        assert callable(asgi_mod.app)

    def test_asgi_app_bukan_api_key_middleware(self):
        """Dengan konfigurasi test (tanpa auth), app tidak dibungkus ApiKeyMiddleware."""
        import budget_sekolah_mcp.asgi as asgi_mod

        assert not isinstance(asgi_mod.app, ApiKeyMiddleware)
