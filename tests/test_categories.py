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


class TestCreateExpenseCategory:
    async def test_creates_on_success(self, mock_client, respx_mock, base_url):
        """create mengembalikan 201 dan data kategori baru."""
        created = {
            "id": 99,
            "code": "5260.01",
            "label": "Biaya Baru",
            "is_operational": True,
            "is_up_component": False,
        }
        respx_mock.post(f"{base_url}/expense-categories").mock(
            return_value=Response(201, json=created)
        )
        response = await mock_client.post(
            "/expense-categories",
            json={"code": "5260.01", "label": "Biaya Baru", "is_operational": True},
        )
        assert response.status_code == 201
        assert response.json()["code"] == "5260.01"

    async def test_returns_409_on_duplicate_code(self, mock_client, respx_mock, base_url):
        """create mengembalikan 409 jika kode sudah ada."""
        respx_mock.post(f"{base_url}/expense-categories").mock(
            return_value=Response(409, json={"detail": "already exists"})
        )
        response = await mock_client.post(
            "/expense-categories", json={"code": "5110.01", "label": "Gaji"}
        )
        assert response.status_code == 409


class TestUpdateExpenseCategory:
    async def test_makes_category_operational(self, mock_client, respx_mock, base_url):
        """update (PUT) dapat menjadikan kategori non-operasional jadi operasional (masuk US)."""
        updated = {
            "id": 50,
            "code": "5580.05",
            "label": "Beasiswa Intern",
            "is_operational": True,
            "is_up_component": False,
            "is_direct_income": False,
        }
        respx_mock.put(f"{base_url}/expense-categories/50").mock(
            return_value=Response(200, json=updated)
        )
        response = await mock_client.put("/expense-categories/50", json={"is_operational": True})
        assert response.status_code == 200
        assert response.json()["is_operational"] is True

    async def test_returns_404_when_missing(self, mock_client, respx_mock, base_url):
        """update mengembalikan 404 jika kategori tidak ditemukan."""
        respx_mock.put(f"{base_url}/expense-categories/9999").mock(
            return_value=Response(404, json={"detail": "not found"})
        )
        response = await mock_client.put("/expense-categories/9999", json={"is_operational": True})
        assert response.status_code == 404


class TestDeleteExpenseCategory:
    async def test_deletes_on_success(self, mock_client, respx_mock, base_url):
        """delete mengembalikan 204 saat berhasil."""
        respx_mock.delete(f"{base_url}/expense-categories/50").mock(return_value=Response(204))
        response = await mock_client.delete("/expense-categories/50")
        assert response.status_code == 204

    async def test_returns_404_when_missing(self, mock_client, respx_mock, base_url):
        """delete mengembalikan 404 jika kategori tidak ditemukan."""
        respx_mock.delete(f"{base_url}/expense-categories/9999").mock(
            return_value=Response(404, json={"detail": "not found"})
        )
        response = await mock_client.delete("/expense-categories/9999")
        assert response.status_code == 404


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
