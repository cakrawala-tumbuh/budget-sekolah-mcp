"""
Fixtures pytest untuk seluruh test suite budget-sekolah-mcp.

Menyediakan:
  mock_client  — Instance BudgetApiClient yang httpx-nya di-intercept respx
  base_url     — Base URL backend dari settings

Semua test menggunakan mock_client sehingga tidak perlu koneksi nyata ke backend.
Token autentikasi di-seed secara manual ke modul auth untuk menghindari kebutuhan
login di setiap test.
"""

import pytest
import respx

from budget_sekolah_mcp import auth
from budget_sekolah_mcp.client import BudgetApiClient
from budget_sekolah_mcp.config import settings


@pytest.fixture(autouse=True)
def seed_auth_token():
    """Seed token JWT dummy ke modul auth sebelum setiap test.

    Menghindari kebutuhan untuk melakukan login nyata ke backend.
    Token direset setelah test selesai.
    """
    auth._access_token = "test-jwt-token"
    yield
    auth._access_token = None


@pytest.fixture
def mock_client():
    """Kembalikan BudgetApiClient siap digunakan dalam test.

    Client dikonfigurasi dengan base_url dari settings. Semua request HTTP
    akan dicegat oleh respx_mock yang di-pass ke test via parameter.

    Returns:
        Instance BudgetApiClient.
    """
    return BudgetApiClient()


@pytest.fixture
def base_url():
    """Kembalikan base URL backend dari settings.

    Returns:
        String base URL tanpa trailing slash.
    """
    return settings.budget_api_base_url.rstrip("/")


@pytest.fixture
def respx_mock():
    """Kembalikan respx MockRouter yang aktif dan meng-intercept semua request httpx.

    Menggunakan respx.mock sebagai context manager sehingga semua request
    httpx AsyncClient dicegat secara otomatis selama test berlangsung.

    Yields:
        Instance respx.MockRouter yang aktif.
    """
    with respx.mock(assert_all_called=False) as mock:
        yield mock
