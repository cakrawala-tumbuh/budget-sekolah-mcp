"""
Unit test untuk tool investments (investasi aset baru).

Menguji operasi list, create, update, dan delete
investasi aset tetap baru beserta kalkulasi depresiasi proporsionalnya.
"""

from httpx import Response

INVESTMENT_DATA = {
    "id": 1,
    "organization_id": 3,
    "investment_category_id": 7,
    "asset_code": "LK-001",
    "asset_name": "Laptop Acer Aspire 5 (30 unit)",
    "purchase_price": 360000000,
    "useful_life": 4,
    "start_month": 7,
    "annual_depreciation": 67500000,
    "proportional_depreciation": 33750000,
}


class TestListInvestments:
    async def test_returns_investments_on_success(self, mock_client, respx_mock, base_url):
        """list_investments mengembalikan list investasi saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/investments").mock(
            return_value=Response(200, json=[INVESTMENT_DATA])
        )
        response = await mock_client.get("/organizations/3/investments")
        assert response.status_code == 200
        assert response.json()[0]["purchase_price"] == 360000000

    async def test_returns_empty_list(self, mock_client, respx_mock, base_url):
        """list_investments mengembalikan list kosong jika belum ada investasi."""
        respx_mock.get(f"{base_url}/organizations/3/investments").mock(
            return_value=Response(200, json=[])
        )
        response = await mock_client.get("/organizations/3/investments")
        assert response.json() == []


class TestCreateInvestment:
    async def test_creates_investment_on_success(self, mock_client, respx_mock, base_url):
        """create_investment mengembalikan data investasi baru saat 201."""
        respx_mock.post(f"{base_url}/organizations/3/investments").mock(
            return_value=Response(201, json=INVESTMENT_DATA)
        )
        response = await mock_client.post(
            "/organizations/3/investments",
            json={
                "investment_category_id": 7,
                "asset_name": "Laptop Acer Aspire 5 (30 unit)",
                "purchase_price": 360000000,
                "useful_life": 4,
                "start_month": 7,
            },
        )
        assert response.status_code == 201
        assert response.json()["proportional_depreciation"] == 33750000

    async def test_returns_422_if_start_month_invalid(self, mock_client, respx_mock, base_url):
        """create_investment mengembalikan 422 jika start_month di luar 1–12."""
        respx_mock.post(f"{base_url}/organizations/3/investments").mock(
            return_value=Response(422, json={"detail": "start_month must be 1-12"})
        )
        response = await mock_client.post(
            "/organizations/3/investments",
            json={
                "investment_category_id": 7,
                "asset_name": "X",
                "purchase_price": 1000,
                "useful_life": 4,
                "start_month": 13,
            },
        )
        assert response.status_code == 422


class TestDeleteInvestment:
    async def test_deletes_investment_on_success(self, mock_client, respx_mock, base_url):
        """delete_investment mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/3/investments/1").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete("/organizations/3/investments/1")
        assert response.status_code == 204

    async def test_returns_404_if_not_found(self, mock_client, respx_mock, base_url):
        """delete_investment mengembalikan 404 jika investasi tidak ada."""
        respx_mock.delete(f"{base_url}/organizations/3/investments/999").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )
        response = await mock_client.delete("/organizations/3/investments/999")
        assert response.status_code == 404
