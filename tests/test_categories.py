"""
Unit test untuk tool categories (kategori biaya, pendapatan, investasi).

Menguji operasi read-only: list_expense_categories, list_income_categories,
dan list_investment_categories.
"""

from httpx import Response

EXPENSE_CATS = [
    {"id": 1, "account_code": "5110.01", "name": "Gaji", "category_type": "OPERATIONAL"},
    {
        "id": 2,
        "account_code": "5590.01",
        "name": "Kontribusi Pusat UP",
        "category_type": "NON_OPERATIONAL",
    },
]

INCOME_CATS = [
    {"id": 1, "account_code": "4110.01", "name": "Uang Pangkal"},
    {"id": 2, "account_code": "4120.01", "name": "Uang Sekolah"},
    {"id": 3, "account_code": "4120.03", "name": "Uang Mandarin"},
]

INVESTMENT_CATS = [
    {"id": 1, "account_code": "1330.01", "name": "Kendaraan"},
    {"id": 7, "account_code": "1330.07", "name": "Lab Komputer"},
]


class TestListExpenseCategories:
    async def test_returns_all_categories(self, mock_client, respx_mock, base_url):
        """list_expense_categories mengembalikan semua kategori biaya saat 200."""
        respx_mock.get(f"{base_url}/expense-categories").mock(
            return_value=Response(200, json=EXPENSE_CATS)
        )
        response = await mock_client.get("/expense-categories")
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["account_code"] == "5110.01"

    async def test_includes_non_operational_category(self, mock_client, respx_mock, base_url):
        """list_expense_categories mencakup kategori non-operasional (5590.xx)."""
        respx_mock.get(f"{base_url}/expense-categories").mock(
            return_value=Response(200, json=EXPENSE_CATS)
        )
        response = await mock_client.get("/expense-categories")
        non_ops = [c for c in response.json() if c["category_type"] == "NON_OPERATIONAL"]
        assert len(non_ops) == 1

    async def test_returns_error_on_server_failure(self, mock_client, respx_mock, base_url):
        """list_expense_categories mengembalikan status 500 jika server error."""
        respx_mock.get(f"{base_url}/expense-categories").mock(
            return_value=Response(500, text="Internal Server Error")
        )
        response = await mock_client.get("/expense-categories")
        assert response.status_code == 500


class TestListIncomeCategories:
    async def test_returns_all_income_categories(self, mock_client, respx_mock, base_url):
        """list_income_categories mengembalikan semua kategori pendapatan saat 200."""
        respx_mock.get(f"{base_url}/income-categories").mock(
            return_value=Response(200, json=INCOME_CATS)
        )
        response = await mock_client.get("/income-categories")
        assert response.status_code == 200
        assert len(response.json()) == 3

    async def test_includes_manual_income_category(self, mock_client, respx_mock, base_url):
        """list_income_categories mencakup akun pendapatan manual (Mandarin, dsb.)."""
        respx_mock.get(f"{base_url}/income-categories").mock(
            return_value=Response(200, json=INCOME_CATS)
        )
        response = await mock_client.get("/income-categories")
        codes = [c["account_code"] for c in response.json()]
        assert "4120.03" in codes


class TestListInvestmentCategories:
    async def test_returns_all_investment_categories(self, mock_client, respx_mock, base_url):
        """list_investment_categories mengembalikan semua kategori investasi saat 200."""
        respx_mock.get(f"{base_url}/investment-categories").mock(
            return_value=Response(200, json=INVESTMENT_CATS)
        )
        response = await mock_client.get("/investment-categories")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_includes_lab_komputer_category(self, mock_client, respx_mock, base_url):
        """list_investment_categories mencakup kategori Lab Komputer (1330.07)."""
        respx_mock.get(f"{base_url}/investment-categories").mock(
            return_value=Response(200, json=INVESTMENT_CATS)
        )
        response = await mock_client.get("/investment-categories")
        codes = [c["account_code"] for c in response.json()]
        assert "1330.07" in codes
