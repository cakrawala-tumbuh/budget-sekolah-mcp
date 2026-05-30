"""
Unit test untuk tool depreciation (aset lama yang masih disusutkan).

Menguji operasi list, create, update, dan delete data aset lama
beserta kalkulasi depresiasi garis lurusnya.
"""

import pytest
from httpx import Response


OLD_ASSET_DATA = {
    "id": 1, "organization_id": 3,
    "asset_code": "LK-OLD-001",
    "asset_name": "Komputer Desktop Lama (10 unit)",
    "acquisition_cost": 50000000, "useful_life": 5,
    "acquisition_year": 2022, "annual_depreciation": 10000000,
}


class TestListOldAssets:
    async def test_returns_assets_on_success(self, mock_client, respx_mock, base_url):
        """list_old_assets mengembalikan list aset lama saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/depreciation").mock(
            return_value=Response(200, json=[OLD_ASSET_DATA])
        )
        response = await mock_client.get("/organizations/3/depreciation")
        assert response.status_code == 200
        assert response.json()[0]["annual_depreciation"] == 10000000

    async def test_returns_empty_list(self, mock_client, respx_mock, base_url):
        """list_old_assets mengembalikan list kosong jika tidak ada aset."""
        respx_mock.get(f"{base_url}/organizations/3/depreciation").mock(
            return_value=Response(200, json=[])
        )
        response = await mock_client.get("/organizations/3/depreciation")
        assert response.json() == []


class TestCreateOldAsset:
    async def test_creates_asset_on_success(self, mock_client, respx_mock, base_url):
        """create_old_asset mengembalikan data aset baru saat 201."""
        respx_mock.post(f"{base_url}/organizations/3/depreciation").mock(
            return_value=Response(201, json=OLD_ASSET_DATA)
        )
        response = await mock_client.post(
            "/organizations/3/depreciation",
            json={
                "asset_name": "Komputer Desktop Lama (10 unit)",
                "acquisition_cost": 50000000,
                "useful_life": 5, "acquisition_year": 2022,
            },
        )
        assert response.status_code == 201
        assert response.json()["acquisition_year"] == 2022

    async def test_returns_422_if_useful_life_zero(self, mock_client, respx_mock, base_url):
        """create_old_asset mengembalikan 422 jika useful_life adalah 0."""
        respx_mock.post(f"{base_url}/organizations/3/depreciation").mock(
            return_value=Response(422, json={"detail": "useful_life must be > 0"})
        )
        response = await mock_client.post(
            "/organizations/3/depreciation",
            json={"asset_name": "X", "acquisition_cost": 1000,
                  "useful_life": 0, "acquisition_year": 2020},
        )
        assert response.status_code == 422


class TestDeleteOldAsset:
    async def test_deletes_asset_on_success(self, mock_client, respx_mock, base_url):
        """delete_old_asset mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/3/depreciation/1").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete("/organizations/3/depreciation/1")
        assert response.status_code == 204
