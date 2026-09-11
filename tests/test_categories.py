"""
Unit test untuk tool categories (kategori biaya, pendapatan, investasi).

Menguji operasi read-only: list_expense_categories, list_income_categories,
list_investment_categories; serta operasi tulis update_income_category
(dipanggil via fastmcp.Client in-memory agar logika partial-update di
dalam tool benar-benar teruji, bukan hanya dipalsukan ulang di test).
"""

import json

from fastmcp import Client, FastMCP
from httpx import Response

from budget_sekolah_mcp.tools import categories

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
    {"id": 1, "account_code": "4110.01", "name": "Uang Pangkal", "is_operational": True},
    {"id": 2, "account_code": "4120.01", "name": "Uang Sekolah", "is_operational": True},
    {"id": 3, "account_code": "4120.03", "name": "Uang Mandarin", "is_operational": False},
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

    async def test_returns_is_operational_for_each_category(
        self, mock_client, respx_mock, base_url
    ):
        """list_income_categories mengembalikan is_operational pada tiap entri."""
        respx_mock.get(f"{base_url}/income-categories").mock(
            return_value=Response(200, json=INCOME_CATS)
        )
        response = await mock_client.get("/income-categories")
        items = response.json()
        assert len(items) == 3
        assert all("is_operational" in item for item in items)
        non_operational = [item for item in items if item["is_operational"] is False]
        assert [item["account_code"] for item in non_operational] == ["4120.03"]


class TestUpdateIncomeCategory:
    """Menguji tool update_income_category secara in-memory via fastmcp.Client.

    Dipanggil lewat Client (bukan langsung memanggil client.put dengan
    payload buatan test) supaya logika partial-update di dalam tool
    (field yang tidak disebut pemanggil tidak ikut terkirim) benar-benar
    diverifikasi, sesuai Skenario Uji issue.
    """

    def _mcp(self, mock_client):
        mcp = FastMCP(name="test")
        categories.register(mcp, mock_client)
        return mcp

    async def test_sends_put_with_is_operational_in_payload(
        self, mock_client, respx_mock, base_url
    ):
        """is_operational=False memanggil PUT /income-categories/{id} dengan muatan itu."""
        updated = {
            "id": 28,
            "code": "TEMP.001",
            "label": "Pendapatan Kantin",
            "is_operational": False,
            "sort_order": 0,
        }
        route = respx_mock.put(f"{base_url}/income-categories/28").mock(
            return_value=Response(200, json=updated)
        )

        mcp = self._mcp(mock_client)
        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_income_category", {"category_id": 28, "is_operational": False}
            )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"is_operational": False}
        assert result.data["is_operational"] is False

    async def test_omitted_fields_not_sent_in_payload(self, mock_client, respx_mock, base_url):
        """Memanggil hanya dengan label tidak menyertakan is_operational di muatan."""
        updated = {
            "id": 3,
            "code": "4120.03",
            "label": "Uang Mandarin Baru",
            "is_operational": True,
            "sort_order": 0,
        }
        route = respx_mock.put(f"{base_url}/income-categories/3").mock(
            return_value=Response(200, json=updated)
        )

        mcp = self._mcp(mock_client)
        async with Client(mcp) as client:
            await client.call_tool(
                "update_income_category", {"category_id": 3, "label": "Uang Mandarin Baru"}
            )

        body = json.loads(route.calls.last.request.content)
        assert body == {"label": "Uang Mandarin Baru"}
        assert "is_operational" not in body
        assert "sort_order" not in body

    async def test_returns_error_dict_when_category_not_found(
        self, mock_client, respx_mock, base_url
    ):
        """404 dari backend menghasilkan dict {error, context}, bukan exception."""
        respx_mock.put(f"{base_url}/income-categories/9999").mock(
            return_value=Response(404, json={"detail": "Income category not found"})
        )

        mcp = self._mcp(mock_client)
        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_income_category", {"category_id": 9999, "is_operational": False}
            )

        assert "error" in result.data
        assert "context" in result.data
        assert result.data["context"]["category_id"] == 9999


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
