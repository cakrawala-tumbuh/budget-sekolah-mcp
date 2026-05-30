"""
Unit test untuk tool budget_entries (entri biaya).

Menguji operasi list, create, bulk create, update, delete entri biaya
operasional dan non-operasional.
"""

import pytest
from httpx import Response


ENTRY_DATA = {
    "id": 1, "organization_id": 3, "expense_category_id": 5,
    "line_number": 1, "description": "Gaji guru",
    "basis": "24 × 12 × 3.500.000", "foundation": 1008000000,
    "bos": 0, "total": 1008000000, "notes": None,
}


class TestListBudgetEntries:
    async def test_returns_entries_on_success(self, mock_client, respx_mock, base_url):
        """list_budget_entries mengembalikan list entri biaya saat 200."""
        respx_mock.get(f"{base_url}/organizations/3/budget-entries").mock(
            return_value=Response(200, json=[ENTRY_DATA])
        )
        response = await mock_client.get("/organizations/3/budget-entries")
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_returns_empty_list(self, mock_client, respx_mock, base_url):
        """list_budget_entries mengembalikan list kosong jika tidak ada entri."""
        respx_mock.get(f"{base_url}/organizations/3/budget-entries").mock(
            return_value=Response(200, json=[])
        )
        response = await mock_client.get("/organizations/3/budget-entries")
        assert response.json() == []


class TestCreateBudgetEntry:
    async def test_creates_entry_on_success(self, mock_client, respx_mock, base_url):
        """create_budget_entry mengembalikan entri baru saat 201."""
        respx_mock.post(f"{base_url}/organizations/3/budget-entries").mock(
            return_value=Response(201, json=ENTRY_DATA)
        )
        response = await mock_client.post(
            "/organizations/3/budget-entries",
            json={
                "expense_category_id": 5, "line_number": 1,
                "description": "Gaji guru", "foundation": 1008000000,
            },
        )
        assert response.status_code == 201
        assert response.json()["foundation"] == 1008000000

    async def test_returns_422_on_validation_error(self, mock_client, respx_mock, base_url):
        """create_budget_entry mengembalikan 422 jika payload tidak valid."""
        respx_mock.post(f"{base_url}/organizations/3/budget-entries").mock(
            return_value=Response(422, json={"detail": "Validation error"})
        )
        response = await mock_client.post(
            "/organizations/3/budget-entries",
            json={"expense_category_id": 5},  # line_number & description missing
        )
        assert response.status_code == 422


class TestBulkCreateBudgetEntries:
    async def test_bulk_creates_entries(self, mock_client, respx_mock, base_url):
        """bulk_create_budget_entries mengembalikan list entri yang dibuat."""
        bulk_result = {"created": 2, "items": [ENTRY_DATA, {**ENTRY_DATA, "id": 2, "line_number": 2}]}
        respx_mock.post(f"{base_url}/organizations/3/budget-entries/bulk").mock(
            return_value=Response(201, json=bulk_result)
        )
        response = await mock_client.post(
            "/organizations/3/budget-entries/bulk",
            json={"entries": [{"expense_category_id": 5, "line_number": 1, "description": "a",
                               "foundation": 1000, "bos": 0}]},
        )
        assert response.status_code == 201
        assert response.json()["created"] == 2


class TestDeleteBudgetEntryByCategory:
    async def test_deletes_by_category(self, mock_client, respx_mock, base_url):
        """delete_budget_entries_by_category mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/3/budget-entries/by-category/5").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete(
            "/organizations/3/budget-entries/by-category/5"
        )
        assert response.status_code == 204
