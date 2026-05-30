"""
Konfigurasi aplikasi via pydantic-settings.

Semua variabel dibaca dari file .env atau environment system.
Instansiasi Settings dilakukan sekali di modul ini dan diimpor
dari tempat lain (singleton pattern).

Variabel wajib:
  BUDGET_API_BASE_URL        — URL backend yang dituju
  BUDGET_API_USERNAME        — username login ke backend
  BUDGET_API_PASSWORD        — password login ke backend

Variabel opsional (OAuth via GitHub — untuk Claude.ai):
  MCP_BASE_URL               — URL publik MCP server.
                               Wajib diisi agar OAuth berfungsi.
                               Contoh: https://mcp.budget-26.cantum-ypii.com
  GITHUB_CLIENT_ID           — Client ID dari GitHub OAuth App.
  GITHUB_CLIENT_SECRET       — Client Secret dari GitHub OAuth App.
  GITHUB_ALLOWED_USERNAMES   — Username GitHub yang diizinkan, dipisah koma.
                               Contoh: "andhit-r" atau "andhit-r,user2".
                               Kosong = semua GitHub user diizinkan.

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
        github_client_id: Client ID dari GitHub OAuth App.
            Jika diisi bersama ``github_client_secret`` dan ``mcp_base_url``,
            server mengaktifkan OAuth via GitHub sebagai identity provider.
        github_client_secret: Client Secret dari GitHub OAuth App.
        github_allowed_usernames: Daftar GitHub username yang diizinkan,
            dipisah koma. Contoh: ``"andhit-r"`` atau ``"andhit-r,user2"``.
            Kosong = semua GitHub user diizinkan (tidak disarankan untuk
            deployment publik).
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
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_allowed_usernames: list[str] = []
    mcp_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
