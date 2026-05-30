"""
Unit test untuk tool income_entries (entri pendapatan manual).

Menguji operasi list, create, bulk create, update, dan delete
entri pendapatan yang tidak dihitung otomatis oleh sistem.
"""

import pytest
from httpx import Response


INCOME_ENTRY = {
    "id": 1, "organization_id": 3, "income_category_id": 8,
    "line_number": 1, "description": "Program Mandarin kelas 1-6",
    "basis": "316 siswa × Rp 100.000", "amount": 31600000, "notes": None,
}


class TestListIncomeEntries:
    async def test_returns_entries_on_success(self, mock_client, respx_mock, base_url):
        """list_income_entries mengembalikan list entri pendapatan saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/income-entries").mock(
            return_value=Response(200, json=[INCOME_ENTRY])
        )
        response = await mock_client.get("/organizations/3/income-entries")
        assert response.status_code == 200
        assert response.json()[0]["amount"] == 31600000

    async def test_returns_404_if_org_missing(self, mock_client, respx_mock, base_url):
        """list_income_entries mengembalikan 404 jika org tidak ditemukan."""
        respx_mock.get(f"{base_url}/organizations/999/income-entries").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )
        response = await mock_client.get("/organizations/999/income-entries")
        assert response.status_code == 404


class TestCreateIncomeEntry:
    async def test_creates_entry_on_success(self, mock_client, respx_mock, base_url):
        """create_income_entry mengembalikan entri baru saat 201."""
        respx_mock.post(f"{base_url}/organizations/3/income-entries").mock(
            return_value=Response(201, json=INCOME_ENTRY)
        )
        response = await mock_client.post(
            "/organizations/3/income-entries",
            json={
                "income_category_id": 8, "line_number": 1,
                "description": "Program Mandarin kelas 1-6", "amount": 31600000,
            },
        )
        assert response.status_code == 201


class TestBulkCreateIncomeEntries:
    async def test_bulk_creates_entries(self, mock_client, respx_mock, base_url):
        """bulk_create_income_entries mengembalikan jumlah entri yang dibuat."""
        bulk_result = {"created": 1, "items": [INCOME_ENTRY]}
        respx_mock.post(f"{base_url}/organizations/3/income-entries/bulk").mock(
            return_value=Response(201, json=bulk_result)
        )
        response = await mock_client.post(
            "/organizations/3/income-entries/bulk",
            json={"entries": [{"income_category_id": 8, "line_number": 1,
                               "description": "Mandarin", "amount": 31600000}]},
        )
        assert response.status_code == 201
        assert response.json()["created"] == 1


class TestDeleteIncomeEntry:
    async def test_deletes_entry_on_success(self, mock_client, respx_mock, base_url):
        """delete_income_entry mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/3/income-entries/1").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete("/organizations/3/income-entries/1")
        assert response.status_code == 204
