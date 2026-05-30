"""
Unit test untuk mekanisme autentikasi server.

Menguji komponen-komponen auth yang baru:

  - GithubUsernameFilteredProvider: filter username GitHub
  - BearerApiKeyVerifier: validasi static API key
  - Logika pemilihan auth di server.py berdasarkan konfigurasi
  - asgi.py menghasilkan ASGI app yang benar

Catatan: Test ini tidak membutuhkan koneksi GitHub nyata —
semua HTTP call ke GitHub API di-mock via respx.
"""

import pytest

from budget_sekolah_mcp.auth_provider import BearerApiKeyVerifier
from budget_sekolah_mcp.middleware import ApiKeyMiddleware


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


class TestGithubUsernameFilteredProvider:
    """Test GithubUsernameFilteredProvider — filter login GitHub."""

    def test_inisialisasi_dengan_satu_username(self):
        """Provider harus bisa dibuat dengan satu username yang diizinkan."""
        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=["andhit-r"],
        )
        assert provider is not None
        assert "andhit-r" in provider._allowed_usernames

    def test_inisialisasi_username_dinormalisasi_lowercase(self):
        """Username harus disimpan dalam lowercase."""
        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=["AndhiT-R", "UserDua"],
        )
        assert "andhit-r" in provider._allowed_usernames
        assert "userdua" in provider._allowed_usernames
        assert "AndhiT-R" not in provider._allowed_usernames

    def test_inisialisasi_tanpa_whitelist_diizinkan(self):
        """Provider harus bisa dibuat tanpa daftar username (semua diizinkan)."""
        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=[],
        )
        assert len(provider._allowed_usernames) == 0

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_username_diizinkan(self, respx_mock):
        """_extract_upstream_claims harus mengembalikan claims jika username diizinkan."""
        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        import httpx
        respx_mock.get("https://api.github.com/user").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 12345,
                    "login": "andhit-r",
                    "name": "Andhit",
                    "email": "andhit@example.com",
                },
            )
        )

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=["andhit-r"],
        )
        claims = await provider._extract_upstream_claims(
            {"access_token": "gho_test_token"}
        )

        assert claims is not None
        assert claims["login"] == "andhit-r"
        assert claims["github_id"] == 12345

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_username_tidak_diizinkan(self, respx_mock):
        """_extract_upstream_claims harus raise TokenError jika username tidak diizinkan."""
        from mcp.server.auth.provider import TokenError

        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        import httpx
        respx_mock.get("https://api.github.com/user").mock(
            return_value=httpx.Response(
                200,
                json={"id": 99999, "login": "orang-lain", "name": "Orang Lain"},
            )
        )

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=["andhit-r"],
        )
        with pytest.raises(TokenError) as exc_info:
            await provider._extract_upstream_claims({"access_token": "gho_test_token"})

        assert exc_info.value.error == "access_denied"
        assert "orang-lain" in exc_info.value.error_description

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_tanpa_whitelist_semua_diizinkan(
        self, respx_mock
    ):
        """Jika allowed_usernames kosong, semua GitHub user harus diizinkan."""
        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        import httpx
        respx_mock.get("https://api.github.com/user").mock(
            return_value=httpx.Response(
                200,
                json={"id": 11111, "login": "siapapun", "name": "Siapapun"},
            )
        )

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=[],
        )
        claims = await provider._extract_upstream_claims(
            {"access_token": "gho_test_token"}
        )

        assert claims is not None
        assert claims["login"] == "siapapun"

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_github_api_error(self, respx_mock):
        """_extract_upstream_claims harus raise TokenError jika GitHub API error."""
        from mcp.server.auth.provider import TokenError

        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        import httpx
        respx_mock.get("https://api.github.com/user").mock(
            return_value=httpx.Response(401, json={"message": "Bad credentials"})
        )

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=["andhit-r"],
        )
        with pytest.raises(TokenError) as exc_info:
            await provider._extract_upstream_claims({"access_token": "gho_invalid"})

        assert exc_info.value.error == "access_denied"

    @pytest.mark.asyncio
    async def test_extract_upstream_claims_tanpa_access_token(self):
        """_extract_upstream_claims harus raise TokenError jika access_token tidak ada."""
        from mcp.server.auth.provider import TokenError

        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=["andhit-r"],
        )
        with pytest.raises(TokenError) as exc_info:
            await provider._extract_upstream_claims({})

        assert exc_info.value.error == "access_denied"


class TestServerAuthMode:
    """Test pemilihan auth mode di server.py berdasarkan konfigurasi."""

    def test_auth_none_di_lingkungan_test(self):
        """Di lingkungan test (tanpa GitHub env vars), _auth harus None."""
        import budget_sekolah_mcp.server as server_mod

        assert server_mod._auth is None

    def test_bearer_verifier_adalah_token_verifier(self):
        """BearerApiKeyVerifier harus merupakan subclass dari TokenVerifier."""
        from fastmcp.server.auth import TokenVerifier

        from budget_sekolah_mcp.auth_provider import BearerApiKeyVerifier

        verifier = BearerApiKeyVerifier(api_key="test")
        assert isinstance(verifier, TokenVerifier)

    def test_github_provider_adalah_subclass_github_provider(self):
        """GithubUsernameFilteredProvider harus merupakan subclass GitHubProvider."""
        from fastmcp.server.auth.providers.github import GitHubProvider

        from budget_sekolah_mcp.auth_provider import GithubUsernameFilteredProvider

        provider = GithubUsernameFilteredProvider(
            client_id="Ov23li_test",
            client_secret="test_secret",
            base_url="https://mcp.example.com",
            allowed_usernames=["andhit-r"],
        )
        assert isinstance(provider, GitHubProvider)


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
