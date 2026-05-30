"""
Unit test untuk ApiKeyMiddleware.

Menguji semua skenario autentikasi tanpa melibatkan FastMCP atau backend:
  - Request tanpa API key → 401
  - Request dengan kunci benar via X-API-Key → diteruskan
  - Request dengan kunci benar via Authorization Bearer → diteruskan
  - Request dengan kunci salah → 401
  - Scope non-HTTP (lifespan) → diteruskan tanpa pemeriksaan
  - Kunci dengan spasi di sekitarnya (strip) → diteruskan
  - Middleware tidak aktif (tidak diinstansiasi) → semua request lewat
"""

import json

import pytest

from budget_sekolah_mcp.middleware import ApiKeyMiddleware

VALID_KEY = "test-secret-api-key-12345"


# ── Helper ASGI app ───────────────────────────────────────────────────────────


class MockApp:
    """ASGI app tiruan yang mencatat apakah ia dipanggil dan mengembalikan 200."""

    def __init__(self) -> None:
        self.called = False
        self.last_scope: dict | None = None

    async def __call__(self, scope, receive, send) -> None:
        self.called = True
        self.last_scope = scope
        if scope["type"] == "http":
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send({"type": "http.response.body", "body": b'{"ok": true}'})


def _make_scope(headers: list[tuple[bytes, bytes]] | None = None, path: str = "/") -> dict:
    """Buat ASGI HTTP scope minimal untuk testing."""
    return {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers or [],
        "client": ("127.0.0.1", 9999),
    }


async def _collect_response(middleware, scope, body=b"") -> tuple[int, bytes]:
    """Jalankan middleware dan kumpulkan status + body dari response."""
    events: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(event):
        events.append(event)

    await middleware(scope, receive, send)

    status = next((e["status"] for e in events if e["type"] == "http.response.start"), 0)
    response_body = next((e["body"] for e in events if e["type"] == "http.response.body"), b"")
    return status, response_body


# ── Test cases ────────────────────────────────────────────────────────────────


class TestApiKeyMiddleware:
    """Test suite untuk ApiKeyMiddleware."""

    @pytest.fixture
    def mock_app(self) -> MockApp:
        return MockApp()

    @pytest.fixture
    def middleware(self, mock_app: MockApp) -> ApiKeyMiddleware:
        return ApiKeyMiddleware(mock_app, api_key=VALID_KEY)

    # ── Kasus penolakan ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_request_tanpa_header_ditolak_401(self, middleware, mock_app):
        """Request tanpa header auth apapun harus mendapat 401."""
        scope = _make_scope(headers=[])
        status, body = await _collect_response(middleware, scope)

        assert status == 401
        assert mock_app.called is False
        data = json.loads(body)
        assert data["error"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_request_kunci_salah_ditolak_401(self, middleware, mock_app):
        """Request dengan API key yang salah harus mendapat 401."""
        scope = _make_scope(headers=[(b"x-api-key", b"kunci-salah")])
        status, _ = await _collect_response(middleware, scope)

        assert status == 401
        assert mock_app.called is False

    @pytest.mark.asyncio
    async def test_bearer_kunci_salah_ditolak_401(self, middleware, mock_app):
        """Request dengan Bearer token yang salah harus mendapat 401."""
        scope = _make_scope(headers=[(b"authorization", b"Bearer kunci-salah")])
        status, _ = await _collect_response(middleware, scope)

        assert status == 401
        assert mock_app.called is False

    @pytest.mark.asyncio
    async def test_authorization_header_bukan_bearer_ditolak(self, middleware, mock_app):
        """Header Authorization dengan skema selain Bearer harus ditolak."""
        scope = _make_scope(headers=[(b"authorization", b"Basic dXNlcjpwYXNz")])
        status, _ = await _collect_response(middleware, scope)

        assert status == 401
        assert mock_app.called is False

    # ── Kasus diterima ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_x_api_key_valid_diteruskan(self, middleware, mock_app):
        """Request dengan X-API-Key yang benar harus diteruskan ke app."""
        scope = _make_scope(headers=[(b"x-api-key", VALID_KEY.encode())])
        status, _ = await _collect_response(middleware, scope)

        assert status == 200
        assert mock_app.called is True

    @pytest.mark.asyncio
    async def test_authorization_bearer_valid_diteruskan(self, middleware, mock_app):
        """Request dengan Authorization: Bearer yang benar harus diteruskan."""
        scope = _make_scope(headers=[(b"authorization", f"Bearer {VALID_KEY}".encode())])
        status, _ = await _collect_response(middleware, scope)

        assert status == 200
        assert mock_app.called is True

    @pytest.mark.asyncio
    async def test_bearer_case_insensitive(self, middleware, mock_app):
        """Skema 'bearer' (huruf kecil) juga harus diterima."""
        scope = _make_scope(headers=[(b"authorization", f"bearer {VALID_KEY}".encode())])
        status, _ = await _collect_response(middleware, scope)

        assert status == 200
        assert mock_app.called is True

    @pytest.mark.asyncio
    async def test_x_api_key_dengan_spasi_strip(self, middleware, mock_app):
        """Nilai X-API-Key dengan spasi di sekitar kunci harus di-strip dan diterima."""
        scope = _make_scope(headers=[(b"x-api-key", f"  {VALID_KEY}  ".encode())])
        status, _ = await _collect_response(middleware, scope)

        assert status == 200
        assert mock_app.called is True

    # ── Scope non-HTTP ────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_lifespan_scope_diteruskan_tanpa_auth(self, middleware, mock_app):
        """Scope 'lifespan' harus diteruskan tanpa pemeriksaan API key."""
        lifespan_events = iter(
            [
                {"type": "lifespan.startup"},
                {"type": "lifespan.shutdown"},
            ]
        )
        sent_events: list[dict] = []

        async def receive():
            return next(lifespan_events)

        async def send(event):
            sent_events.append(event)

        scope = {"type": "lifespan"}
        await middleware(scope, receive, send)

        assert mock_app.called is True
        assert mock_app.last_scope == scope

    @pytest.mark.asyncio
    async def test_websocket_scope_diteruskan_tanpa_auth(self, middleware, mock_app):
        """Scope 'websocket' harus diteruskan tanpa pemeriksaan API key."""
        scope = {"type": "websocket", "path": "/ws", "headers": []}

        async def receive():
            return {"type": "websocket.connect"}

        async def send(_):
            pass

        await middleware(scope, receive, send)

        assert mock_app.called is True

    # ── Response 401 struktur ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_response_401_memiliki_www_authenticate_header(self, middleware, mock_app):
        """Response 401 harus menyertakan header WWW-Authenticate."""
        scope = _make_scope(headers=[])
        events: list[dict] = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(event):
            events.append(event)

        await middleware(scope, receive, send)

        start_event = next(e for e in events if e["type"] == "http.response.start")
        headers_dict = dict(start_event["headers"])
        assert b"www-authenticate" in headers_dict
        assert b"Bearer" in headers_dict[b"www-authenticate"]

    @pytest.mark.asyncio
    async def test_response_401_content_type_json(self, middleware, mock_app):
        """Response 401 harus memiliki Content-Type application/json."""
        scope = _make_scope(headers=[])
        events: list[dict] = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(event):
            events.append(event)

        await middleware(scope, receive, send)

        start_event = next(e for e in events if e["type"] == "http.response.start")
        headers_dict = dict(start_event["headers"])
        assert b"application/json" in headers_dict[b"content-type"]
