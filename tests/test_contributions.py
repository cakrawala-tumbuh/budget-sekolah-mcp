"""
Unit test untuk tool contributions (tarif kontribusi dan alokasi).

Menguji operasi get/set tarif kontribusi serta operasi list dan upsert
alokasi kontribusi dari unit/cabang ke cabang/pusat.
"""

import pytest
from httpx import Response


RATES_DATA = {
    "id": 1, "organization_id": 3,
    "up_to_pusat": 0.04, "up_to_cabang": 0.12,
    "us_to_pusat": 0.05, "us_to_cabang": 0.10,
    "development_fund": 0.20, "deficit_reserve": 0.05,
    "social_care": 0.03, "teacher_study": 0.03,
}

ALLOCATION_DATA = {
    "id": 1, "organization_id": 2,  # CABANG
    "from_organization_id": 3,       # UNIT
    "total_students": 336, "new_students": 60,
    "override_pct_us": None, "override_pct_up": None,
}


class TestGetContributionRates:
    async def test_returns_rates_on_success(self, mock_client, respx_mock, base_url):
        """get_contribution_rates mengembalikan semua tarif kontribusi saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/contribution-rates").mock(
            return_value=Response(200, json=RATES_DATA)
        )
        response = await mock_client.get("/organizations/3/contribution-rates")
        assert response.status_code == 200
        assert response.json()["up_to_pusat"] == 0.04
        assert response.json()["us_to_cabang"] == 0.10

    async def test_returns_404_if_org_missing(self, mock_client, respx_mock, base_url):
        """get_contribution_rates mengembalikan 404 jika org tidak ada."""
        respx_mock.get(f"{base_url}/organizations/999/contribution-rates").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )
        response = await mock_client.get("/organizations/999/contribution-rates")
        assert response.status_code == 404


class TestSetContributionRates:
    async def test_sets_rates_on_success(self, mock_client, respx_mock, base_url):
        """set_contribution_rates menyimpan tarif dan mengembalikan data tersimpan."""
        updated_rates = {**RATES_DATA, "up_to_pusat": 0.05}
        respx_mock.put(f"{base_url}/organizations/3/contribution-rates").mock(
            return_value=Response(200, json=updated_rates)
        )
        response = await mock_client.put(
            "/organizations/3/contribution-rates",
            json={"up_to_pusat": 0.05, "up_to_cabang": 0.12,
                  "us_to_pusat": 0.05, "us_to_cabang": 0.10,
                  "development_fund": 0.20, "deficit_reserve": 0.05,
                  "social_care": 0.03, "teacher_study": 0.03},
        )
        assert response.status_code == 200
        assert response.json()["up_to_pusat"] == 0.05


class TestListContributionAllocations:
    async def test_returns_allocations_for_cabang(self, mock_client, respx_mock, base_url):
        """list_contribution_allocations mengembalikan list alokasi saat 200."""
        respx_mock.get(f"{base_url}/organizations/2/contribution-allocations").mock(
            return_value=Response(200, json=[ALLOCATION_DATA])
        )
        response = await mock_client.get("/organizations/2/contribution-allocations")
        assert response.status_code == 200
        assert response.json()[0]["from_organization_id"] == 3

    async def test_returns_422_for_unit(self, mock_client, respx_mock, base_url):
        """list_contribution_allocations mengembalikan 422 jika org adalah UNIT."""
        respx_mock.get(f"{base_url}/organizations/3/contribution-allocations").mock(
            return_value=Response(422, json={"detail": "Only CABANG/PUSAT"})
        )
        response = await mock_client.get("/organizations/3/contribution-allocations")
        assert response.status_code == 422


class TestUpsertContributionAllocation:
    async def test_upserts_allocation_on_success(self, mock_client, respx_mock, base_url):
        """upsert_contribution_allocation mengembalikan alokasi yang disimpan."""
        respx_mock.put(f"{base_url}/organizations/2/contribution-allocations").mock(
            return_value=Response(200, json=ALLOCATION_DATA)
        )
        response = await mock_client.put(
            "/organizations/2/contribution-allocations",
            json={"from_organization_id": 3, "total_students": 336, "new_students": 60},
        )
        assert response.status_code == 200
        assert response.json()["total_students"] == 336
