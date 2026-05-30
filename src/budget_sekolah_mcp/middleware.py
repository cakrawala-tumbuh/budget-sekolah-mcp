"""
Middleware ASGI untuk autentikasi API Key pada MCP server.

Digunakan ketika server di-deploy via HTTP/SSE (cloud deployment).
Tidak aktif untuk transport stdio (transport stdio tidak melewati HTTP sama sekali).

Mendukung dua metode autentikasi (pilih salah satu):
  - Header ``X-API-Key: <key>``
  - Header ``Authorization: Bearer <key>``

Keamanan:
  - Perbandingan kunci menggunakan ``hmac.compare_digest`` untuk mencegah
    timing attack.
  - Permintaan tanpa kunci atau dengan kunci salah mendapat respons 401.
  - Scope non-HTTP (lifespan, websocket) diteruskan tanpa pemeriksaan.
"""

import hmac
import json
import logging

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class ApiKeyMiddleware:
    """Pure ASGI middleware untuk validasi API Key pada setiap HTTP request.

    Memeriksa header ``X-API-Key`` atau ``Authorization: Bearer`` pada setiap
    request HTTP. Request non-HTTP (lifespan, websocket) diteruskan langsung
    tanpa pemeriksaan sehingga tidak mengganggu siklus hidup server.

    Menggunakan ``hmac.compare_digest`` untuk membandingkan kunci secara
    constant-time, mencegah serangan timing attack.

    Attributes:
        app: ASGI app yang dibungkus middleware ini.
        api_key: API key valid yang harus disertakan oleh klien.

    Example:
        >>> from starlette.testclient import TestClient
        >>> base_app = ...  # ASGI app
        >>> secured_app = ApiKeyMiddleware(base_app, api_key="secret-key")
        >>> client = TestClient(secured_app, raise_server_exceptions=False)
        >>> r = client.get("/", headers={"X-API-Key": "secret-key"})
        >>> r.status_code
        200
    """

    def __init__(self, app: ASGIApp, api_key: str) -> None:
        """Inisialisasi middleware dengan app dan API key.

        Args:
            app: ASGI app yang dibungkus.
            api_key: API key yang harus disertakan oleh setiap klien.
        """
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Proses setiap ASGI event.

        Untuk scope bukan ``http``, diteruskan langsung ke app tanpa validasi.
        Untuk scope ``http``, validasi API key dilakukan sebelum meneruskan request.

        Args:
            scope: ASGI scope dict berisi informasi request.
            receive: ASGI receive callable.
            send: ASGI send callable.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))

        # Header X-API-Key
        x_api_key = headers.get(b"x-api-key", b"").decode("utf-8", errors="ignore").strip()

        # Header Authorization: Bearer <key>
        auth_header = headers.get(b"authorization", b"").decode("utf-8", errors="ignore")
        bearer_key = ""
        if auth_header.lower().startswith("bearer "):
            bearer_key = auth_header[7:].strip()

        provided_key = x_api_key or bearer_key

        if not provided_key or not hmac.compare_digest(provided_key, self.api_key):
            logger.warning(
                "Permintaan ditolak — API key tidak valid atau tidak disertakan. "
                "Path: %s | Client: %s",
                scope.get("path", "unknown"),
                scope.get("client", ("unknown", 0))[0],
            )
            await self._reject_401(send)
            return

        await self.app(scope, receive, send)

    @staticmethod
    async def _reject_401(send: Send) -> None:
        """Kirim respons HTTP 401 Unauthorized.

        Mengirim JSON body yang menjelaskan alasan penolakan beserta
        header ``WWW-Authenticate`` sesuai standar RFC 7235.

        Args:
            send: ASGI send callable.
        """
        body = json.dumps(
            {
                "error": "Unauthorized",
                "detail": (
                    "API key tidak valid atau tidak disertakan. "
                    "Sertakan header 'X-API-Key: <key>' "
                    "atau 'Authorization: Bearer <key>'."
                ),
            }
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"www-authenticate", b'Bearer realm="budget-sekolah-mcp"'),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )
