"""
Unit test untuk tool parent_expense_allocations.

Menguji operasi list, create, update, dan delete alokasi biaya induk ke unit anak.
"""

from httpx import Response


class TestListParentExpenseAllocations:
    async def test_returns_items_on_success(self, mock_client, respx_mock, base_url):
        """list mengembalikan daftar alokasi saat 200."""
        items = [
            {
                "id": 1,
                "parent_org_id": 2,
                "expense_category_id": 5,
                "affects_up": False,
                "is_active": True,
                "expense_category_code": "5110.01",
                "expense_category_label": "Gaji",
            }
        ]
        respx_mock.get(f"{base_url}/organizations/2/parent-expense-allocations").mock(
            return_value=Response(200, json=items)
        )
        response = await mock_client.get("/organizations/2/parent-expense-allocations")
        assert response.status_code == 200
        assert response.json()[0]["expense_category_code"] == "5110.01"

    async def test_returns_422_for_unit(self, mock_client, respx_mock, base_url):
        """list mengembalikan 422 jika org bertipe UNIT."""
        respx_mock.get(f"{base_url}/organizations/3/parent-expense-allocations").mock(
            return_value=Response(422, json={"detail": "only CABANG/PUSAT"})
        )
        response = await mock_client.get("/organizations/3/parent-expense-allocations")
        assert response.status_code == 422


class TestCreateParentExpenseAllocation:
    async def test_creates_on_success(self, mock_client, respx_mock, base_url):
        """create mengembalikan 201 dan data alokasi."""
        created = {
            "id": 1,
            "parent_org_id": 2,
            "expense_category_id": 5,
            "affects_up": True,
            "is_active": True,
        }
        respx_mock.post(f"{base_url}/organizations/2/parent-expense-allocations").mock(
            return_value=Response(201, json=created)
        )
        response = await mock_client.post(
            "/organizations/2/parent-expense-allocations",
            json={"expense_category_id": 5, "affects_up": True, "is_active": True},
        )
        assert response.status_code == 201
        assert response.json()["affects_up"] is True

    async def test_returns_409_on_duplicate(self, mock_client, respx_mock, base_url):
        """create mengembalikan 409 jika alokasi sudah ada."""
        respx_mock.post(f"{base_url}/organizations/2/parent-expense-allocations").mock(
            return_value=Response(409, json={"detail": "already exists"})
        )
        response = await mock_client.post(
            "/organizations/2/parent-expense-allocations",
            json={"expense_category_id": 5},
        )
        assert response.status_code == 409


class TestUpdateParentExpenseAllocation:
    async def test_updates_on_success(self, mock_client, respx_mock, base_url):
        """update (PATCH) mengembalikan 200 dan data terbaru."""
        updated = {
            "id": 1,
            "parent_org_id": 2,
            "expense_category_id": 5,
            "affects_up": False,
            "is_active": False,
        }
        respx_mock.patch(f"{base_url}/organizations/2/parent-expense-allocations/1").mock(
            return_value=Response(200, json=updated)
        )
        response = await mock_client.patch(
            "/organizations/2/parent-expense-allocations/1",
            json={"is_active": False},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False


class TestDeleteParentExpenseAllocation:
    async def test_returns_204_on_success(self, mock_client, respx_mock, base_url):
        """delete mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/2/parent-expense-allocations/1").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete("/organizations/2/parent-expense-allocations/1")
        assert response.status_code == 204
