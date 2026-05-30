"""
Konfigurasi aplikasi via pydantic-settings.

Semua variabel dibaca dari file .env atau environment system.
Instansiasi Settings dilakukan sekali di modul ini dan diimpor
dari tempat lain (singleton pattern).

Variabel wajib:
  BUDGET_API_BASE_URL        — URL backend yang dituju
  BUDGET_API_USERNAME        — username login ke backend
  BUDGET_API_PASSWORD        — password login ke backend

Variabel opsional (OAuth via Authentik — untuk Claude.ai):
  MCP_BASE_URL                  — URL publik MCP server.
                                  Wajib diisi agar OAuth berfungsi.
                                  Contoh: https://mcp.budget-26.cantum-ypii.com
  AUTHENTIK_BASE_URL            — URL dasar Authentik.
                                  Contoh: https://auth.cantum-ypii.com
  AUTHENTIK_APP_SLUG            — Slug OAuth2 Provider di Authentik.
                                  Contoh: budget-mcp
  AUTHENTIK_CLIENT_ID           — Client ID dari Authentik OAuth2 Provider.
  AUTHENTIK_CLIENT_SECRET       — Client Secret dari Authentik OAuth2 Provider.
  AUTHENTIK_ALLOWED_USERNAMES   — preferred_username Authentik yang diizinkan,
                                  dipisah koma. Kosong = semua user diizinkan.

Variabel opsional (API Key — untuk VS Code / tools lain):
  MCP_API_KEY                — API key statis. Request wajib menyertakan
                               header 'Authorization: Bearer <key>'.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurasi runtime MCP server.

    Semua nilai dibaca dari environment variable atau file .env.
    Field dengan default dapat tidak diisi; field tanpa default wajib diisi.

    Attributes:
        budget_api_base_url: Base URL instance budget-backend-ypii.
        budget_api_username: Username untuk login ke backend API.
        budget_api_password: Password untuk login ke backend API.
        mcp_server_name: Nama server MCP yang ditampilkan ke AI client.
        mcp_log_level: Level logging (DEBUG, INFO, WARNING, ERROR).
        http_timeout: Timeout HTTP request dalam detik.
        mcp_base_url: URL publik MCP server. Wajib diisi jika OAuth aktif.
            Contoh: ``https://mcp.budget-26.cantum-ypii.com``.
        authentik_base_url: URL dasar Authentik, contoh
            ``https://auth.cantum-ypii.com``. Jika diisi bersama
            ``authentik_app_slug``, ``authentik_client_id``,
            ``authentik_client_secret``, dan ``mcp_base_url``, server
            mengaktifkan OAuth via Authentik sebagai identity provider.
        authentik_app_slug: Slug OAuth2/OIDC Provider di Authentik,
            contoh ``budget-mcp``.
        authentik_client_id: Client ID dari Authentik OAuth2 Provider.
        authentik_client_secret: Client Secret dari Authentik OAuth2 Provider.
        authentik_allowed_usernames: Daftar ``preferred_username`` Authentik
            yang diizinkan, dalam format JSON array (``["a","b"]``).
            Nilai kosong atau tidak diset = semua user Authentik diizinkan.
        mcp_api_key: API key statis untuk akses dari VS Code dan tools lain
            yang tidak mendukung OAuth. Request wajib menyertakan header
            ``Authorization: Bearer <key>``.
    """

    budget_api_base_url: str
    budget_api_username: str
    budget_api_password: str

    mcp_server_name: str = "budget-sekolah-mcp"
    mcp_log_level: str = "INFO"
    http_timeout: float = 30.0
    mcp_base_url: str | None = None
    authentik_base_url: str | None = None
    authentik_app_slug: str | None = None
    authentik_client_id: str | None = None
    authentik_client_secret: str | None = None
    authentik_allowed_usernames: list[str] = []
    mcp_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
