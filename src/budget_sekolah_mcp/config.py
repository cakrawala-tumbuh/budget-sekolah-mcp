"""
Konfigurasi aplikasi via pydantic-settings.

Semua variabel dibaca dari file .env atau environment system.
Instansiasi Settings dilakukan sekali di modul ini dan diimpor
dari tempat lain (singleton pattern).

Variabel wajib:
  BUDGET_API_BASE_URL  — URL backend yang dituju
  BUDGET_API_USERNAME  — username login ke backend
  BUDGET_API_PASSWORD  — password login ke backend

Variabel opsional:
  MCP_API_KEY          — API key untuk mengamankan MCP server di cloud.
                         Jika diisi, setiap request HTTP/SSE wajib menyertakan
                         header 'X-API-Key: <key>' atau 'Authorization: Bearer <key>'.
                         Kosongkan untuk menonaktifkan autentikasi (lokal/stdio).
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
        mcp_api_key: API key untuk mengamankan endpoint HTTP/SSE. Jika diisi,
            setiap request wajib menyertakan header ``X-API-Key`` atau
            ``Authorization: Bearer``. Kosongkan untuk menonaktifkan (stdio/lokal).
    """

    budget_api_base_url: str
    budget_api_username: str
    budget_api_password: str

    mcp_server_name: str = "budget-sekolah-mcp"
    mcp_log_level: str = "INFO"
    http_timeout: float = 30.0
    mcp_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
