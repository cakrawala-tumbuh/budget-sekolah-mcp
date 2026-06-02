"""
Unit test untuk tool subsidies.

Menguji operasi list, create, update, dan delete subsidi dari CABANG/PUSAT
ke organisasi penerima.
"""

from httpx import Response


class TestListSubsidies:
    async def test_returns_items_on_success(self, mock_client, respx_mock, base_url):
        """list mengembalikan daftar subsidi saat 200."""
        items = [
            {
                "id": 1,
                "provider_org_id": 2,
                "recipient_org_id": 3,
                "recipient_org_name": "SD MBL",
                "expense_category_id": 5,
                "income_category_id": 7,
                "amount": 1000000.0,
                "is_active": True,
            }
        ]
        respx_mock.get(f"{base_url}/organizations/2/subsidies").mock(
            return_value=Response(200, json=items)
        )
        response = await mock_client.get("/organizations/2/subsidies")
        assert response.status_code == 200
        assert response.json()[0]["amount"] == 1000000.0

    async def test_returns_422_for_unit(self, mock_client, respx_mock, base_url):
        """list mengembalikan 422 jika pemberi bertipe UNIT."""
        respx_mock.get(f"{base_url}/organizations/3/subsidies").mock(
            return_value=Response(422, json={"detail": "only CABANG/PUSAT"})
        )
        response = await mock_client.get("/organizations/3/subsidies")
        assert response.status_code == 422


class TestCreateSubsidy:
    async def test_creates_on_success(self, mock_client, respx_mock, base_url):
        """create mengembalikan 201 dan data subsidi."""
        created = {
            "id": 1,
            "provider_org_id": 2,
            "recipient_org_id": 3,
            "expense_category_id": 5,
            "income_category_id": 7,
            "amount": 500000.0,
            "is_active": True,
        }
        respx_mock.post(f"{base_url}/organizations/2/subsidies").mock(
            return_value=Response(201, json=created)
        )
        response = await mock_client.post(
            "/organizations/2/subsidies",
            json={
                "recipient_org_id": 3,
                "expense_category_id": 5,
                "income_category_id": 7,
                "amount": 500000.0,
                "is_active": True,
            },
        )
        assert response.status_code == 201
        assert response.json()["amount"] == 500000.0

    async def test_returns_422_for_invalid_recipient(self, mock_client, respx_mock, base_url):
        """create mengembalikan 422 jika penerima tidak valid."""
        respx_mock.post(f"{base_url}/organizations/2/subsidies").mock(
            return_value=Response(422, json={"detail": "CABANG hanya ke UNIT anaknya"})
        )
        response = await mock_client.post(
            "/organizations/2/subsidies",
            json={"recipient_org_id": 9, "expense_category_id": 5, "income_category_id": 7},
        )
        assert response.status_code == 422


class TestUpdateSubsidy:
    async def test_updates_on_success(self, mock_client, respx_mock, base_url):
        """update (PATCH) mengembalikan 200 dan data terbaru."""
        updated = {
            "id": 1,
            "provider_org_id": 2,
            "recipient_org_id": 3,
            "expense_category_id": 5,
            "income_category_id": 7,
            "amount": 750000.0,
            "is_active": True,
        }
        respx_mock.patch(f"{base_url}/organizations/2/subsidies/1").mock(
            return_value=Response(200, json=updated)
        )
        response = await mock_client.patch(
            "/organizations/2/subsidies/1", json={"amount": 750000.0}
        )
        assert response.status_code == 200
        assert response.json()["amount"] == 750000.0


class TestDeleteSubsidy:
    async def test_returns_204_on_success(self, mock_client, respx_mock, base_url):
        """delete mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/2/subsidies/1").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete("/organizations/2/subsidies/1")
        assert response.status_code == 204
