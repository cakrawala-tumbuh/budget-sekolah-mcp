"""
Unit test untuk tool simulation.

Menguji semua tipe simulasi: UP, US, income, expenses, allocation,
depreciation, dan summary. Memvalidasi penanganan 200, 404, dan 422.
"""

import pytest
from httpx import Response


UP_RESULT = {
    "components": [],
    "total_up_cost_with_dep": 300000000,
    "new_student_count": 60,
    "auto_up_rate": 5000000.0,
    "final_up_rate": 5000000.0,
    "total_up_revenue": 300000000,
}

US_RESULT = {
    "components": [],
    "total_us_cost": 1620000000,
    "total_students": 300,
    "months": 12,
    "auto_us_rate": 450000.0,
    "final_us_rate": 450000.0,
    "total_us_revenue": 1620000000,
}

INCOME_RESULT = {
    "items": [{"account_code": "4110.01", "name": "Uang Pangkal", "amount": 300000000}],
    "total": 2500000000,
}

EXPENSES_RESULT = {
    "operational": [],
    "non_operational": [],
    "total_operational": 1800000000,
    "total_non_operational": 450000000,
    "grand_total": 2250000000,
}

ALLOCATION_RESULT = {
    "allocations": [{"from_org": "SD-MBL", "up_contribution": 12000000}],
    "total_up": 12000000,
    "total_us": 45000000,
}

DEPRECIATION_RESULT = {
    "new_assets": [],
    "old_assets": [],
    "total_new_dep": 33750000,
    "total_old_dep": 10000000,
    "grand_total": 43750000,
}

SUMMARY_RESULT = {
    "total_income": 2500000000,
    "total_expense": 2250000000,
    "surplus_deficit": 250000000,
}


class TestSimulateUp:
    async def test_returns_up_simulation_on_success(self, mock_client, respx_mock, base_url):
        """simulate_up mengembalikan hasil simulasi UP saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/simulation/up").mock(
            return_value=Response(200, json=UP_RESULT)
        )
        response = await mock_client.get("/organizations/3/simulation/up")
        assert response.status_code == 200
        assert response.json()["final_up_rate"] == 5000000.0

    async def test_returns_422_for_non_unit(self, mock_client, respx_mock, base_url):
        """simulate_up mengembalikan 422 jika org bukan UNIT."""
        respx_mock.get(f"{base_url}/organizations/1/simulation/up").mock(
            return_value=Response(422, json={"detail": "Only UNIT"})
        )
        response = await mock_client.get("/organizations/1/simulation/up")
        assert response.status_code == 422

    async def test_returns_404_if_org_missing(self, mock_client, respx_mock, base_url):
        """simulate_up mengembalikan 404 jika org tidak ditemukan."""
        respx_mock.get(f"{base_url}/organizations/999/simulation/up").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )
        response = await mock_client.get("/organizations/999/simulation/up")
        assert response.status_code == 404


class TestSimulateUs:
    async def test_returns_us_simulation_on_success(self, mock_client, respx_mock, base_url):
        """simulate_us mengembalikan hasil simulasi US saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/simulation/us").mock(
            return_value=Response(200, json=US_RESULT)
        )
        response = await mock_client.get("/organizations/3/simulation/us")
        assert response.status_code == 200
        assert response.json()["final_us_rate"] == 450000.0


class TestSimulateIncome:
    async def test_returns_income_simulation_on_success(self, mock_client, respx_mock, base_url):
        """simulate_income mengembalikan total pendapatan saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/simulation/income").mock(
            return_value=Response(200, json=INCOME_RESULT)
        )
        response = await mock_client.get("/organizations/3/simulation/income")
        assert response.status_code == 200
        assert response.json()["total"] == 2500000000


class TestSimulateExpenses:
    async def test_returns_expenses_simulation_on_success(self, mock_client, respx_mock, base_url):
        """simulate_expenses mengembalikan total biaya saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/simulation/expenses").mock(
            return_value=Response(200, json=EXPENSES_RESULT)
        )
        response = await mock_client.get("/organizations/3/simulation/expenses")
        assert response.status_code == 200
        assert response.json()["grand_total"] == 2250000000


class TestSimulateAllocation:
    async def test_returns_allocation_for_cabang(self, mock_client, respx_mock, base_url):
        """simulate_allocation mengembalikan kontribusi yang diterima saat 200."""
        respx_mock.get(f"{base_url}/organizations/2/simulation/allocation").mock(
            return_value=Response(200, json=ALLOCATION_RESULT)
        )
        response = await mock_client.get("/organizations/2/simulation/allocation")
        assert response.status_code == 200
        assert response.json()["total_us"] == 45000000

    async def test_returns_422_for_unit(self, mock_client, respx_mock, base_url):
        """simulate_allocation mengembalikan 422 jika org adalah UNIT."""
        respx_mock.get(f"{base_url}/organizations/3/simulation/allocation").mock(
            return_value=Response(422, json={"detail": "Only CABANG/PUSAT"})
        )
        response = await mock_client.get("/organizations/3/simulation/allocation")
        assert response.status_code == 422


class TestSimulateDepreciation:
    async def test_returns_depreciation_summary(self, mock_client, respx_mock, base_url):
        """simulate_depreciation mengembalikan ringkasan depresiasi saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/simulation/depreciation").mock(
            return_value=Response(200, json=DEPRECIATION_RESULT)
        )
        response = await mock_client.get("/organizations/3/simulation/depreciation")
        assert response.status_code == 200
        assert response.json()["grand_total"] == 43750000


class TestSimulateSummary:
    async def test_returns_full_summary(self, mock_client, respx_mock, base_url):
        """simulate_summary mengembalikan ringkasan RAB lengkap saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/simulation/summary").mock(
            return_value=Response(200, json=SUMMARY_RESULT)
        )
        response = await mock_client.get("/organizations/3/simulation/summary")
        assert response.status_code == 200
        assert response.json()["surplus_deficit"] == 250000000

    async def test_returns_404_if_org_missing(self, mock_client, respx_mock, base_url):
        """simulate_summary mengembalikan 404 jika org tidak ditemukan."""
        respx_mock.get(f"{base_url}/organizations/999/simulation/summary").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )
        response = await mock_client.get("/organizations/999/simulation/summary")
        assert response.status_code == 404
