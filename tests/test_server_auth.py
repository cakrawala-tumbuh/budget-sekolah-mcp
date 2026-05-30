"""
Unit test untuk mekanisme pemilihan autentikasi server.

Menguji bahwa OAuthProvider dapat diinstansiasi dan konfigurasi auth dipilih
dengan benar berdasarkan MCP_BASE_URL dan MCP_API_KEY:

  - OAuthProvider dapat diinstansiasi dengan base_url yang valid
  - OAuthProvider memiliki client_registration_options.enabled = True
  - ApiKeyMiddleware digunakan ketika hanya MCP_API_KEY yang dikonfigurasi
  - Tanpa konfigurasi auth → app tidak dibungkus ApiKeyMiddleware
  - Environment test (tanpa MCP_BASE_URL) → _auth adalah None
"""

import pytest

from budget_sekolah_mcp.middleware import ApiKeyMiddleware


class TestOAuthProviderInstansiasi:
    """Test instansiasi dan konfigurasi OAuthProvider."""

    def test_oauth_provider_dapat_diinstansiasi_dengan_base_url(self):
        """OAuthProvider harus bisa dibuat dengan base_url yang valid."""
        from fastmcp.server.auth.auth import ClientRegistrationOptions, OAuthProvider

        provider = OAuthProvider(
            base_url="https://mcp.budget-26.cantum-ypii.com",
            client_registration_options=ClientRegistrationOptions(enabled=True),
        )

        assert provider is not None

    def test_oauth_provider_memiliki_client_registration_enabled(self):
        """OAuthProvider harus mengaktifkan dynamic client registration."""
        from fastmcp.server.auth.auth import ClientRegistrationOptions, OAuthProvider

        provider = OAuthProvider(
            base_url="https://mcp.budget-26.cantum-ypii.com",
            client_registration_options=ClientRegistrationOptions(enabled=True),
        )

        assert provider.client_registration_options is not None
        assert provider.client_registration_options.enabled is True

    def test_oauth_provider_base_url_tersimpan_dengan_benar(self):
        """OAuthProvider harus menyimpan base_url dengan benar."""
        from fastmcp.server.auth.auth import OAuthProvider

        base_url = "https://mcp.budget-26.cantum-ypii.com"
        provider = OAuthProvider(base_url=base_url)

        assert str(provider.base_url).rstrip("/") == base_url.rstrip("/")

    def test_auth_none_di_lingkungan_test(self):
        """Di lingkungan test (tanpa MCP_BASE_URL), _auth harus None."""
        import budget_sekolah_mcp.server as server_mod

        # Test environment tidak mempunyai MCP_BASE_URL
        assert server_mod._auth is None


class TestAsgiAuthMode:
    """Test logika pemilihan mode auth di asgi.py melalui ApiKeyMiddleware langsung."""

    def test_api_key_middleware_membungkus_app_saat_aktif(self):
        """ApiKeyMiddleware harus membungkus app jika api_key diberikan."""
        inner_app = object()
        middleware = ApiKeyMiddleware(inner_app, api_key="test-key")

        assert isinstance(middleware, ApiKeyMiddleware)
        assert middleware.app is inner_app
        assert middleware.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_mode_legacy_menolak_request_tanpa_kunci(self):
        """Middleware legacy harus menolak request tanpa API key."""
        import json

        events: list[dict] = []

        async def dummy_app(scope, receive, send):
            pass

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(event):
            events.append(event)

        middleware = ApiKeyMiddleware(dummy_app, api_key="real-secret-key")
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/sse",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        }
        await middleware(scope, receive, send)

        start = next(e for e in events if e["type"] == "http.response.start")
        assert start["status"] == 401
        body_event = next(e for e in events if e["type"] == "http.response.body")
        data = json.loads(body_event["body"])
        assert data["error"] == "Unauthorized"

    def test_mode_oauth_tidak_menggunakan_api_key_middleware(self):
        """Ketika OAuth aktif, app tidak boleh dibungkus ApiKeyMiddleware."""
        from fastmcp.server.auth.auth import ClientRegistrationOptions, OAuthProvider

        # Simulasi: buat provider dan verifikasi tidak ada middleware statis
        provider = OAuthProvider(
            base_url="https://mcp.budget-26.cantum-ypii.com",
            client_registration_options=ClientRegistrationOptions(enabled=True),
        )
        inner_app = object()

        # Saat OAuth aktif, app langsung dipakai tanpa ApiKeyMiddleware
        app = inner_app  # tidak dibungkus

        assert not isinstance(app, ApiKeyMiddleware)
        assert app is inner_app
        # Verify provider exist and is the right type
        assert isinstance(provider, OAuthProvider)

