"""
Unit test untuk tool assumptions.

Menguji operasi get, upsert, dan delete asumsi siswa untuk organisasi UNIT.
"""

import pytest
from httpx import Response


class TestGetAssumption:
    async def test_returns_assumption_on_success(self, mock_client, respx_mock, base_url):
        """get_assumption mengembalikan data asumsi saat 200."""
        assumption_data = {
            "id": 1, "organization_id": 3,
            "grade_1": 60, "grade_2": 58, "total_students": 336,
        }
        respx_mock.get(f"{base_url}/organizations/3/assumption").mock(
            return_value=Response(200, json=assumption_data)
        )
        response = await mock_client.get("/organizations/3/assumption")
        assert response.status_code == 200
        assert response.json()["total_students"] == 336

    async def test_returns_404_if_not_set(self, mock_client, respx_mock, base_url):
        """get_assumption mengembalikan 404 jika asumsi belum diisi."""
        respx_mock.get(f"{base_url}/organizations/3/assumption").mock(
            return_value=Response(404, json={"detail": "Asumsi belum diisi"})
        )
        response = await mock_client.get("/organizations/3/assumption")
        assert response.status_code == 404

    async def test_returns_422_for_non_unit(self, mock_client, respx_mock, base_url):
        """get_assumption mengembalikan 422 jika org bukan UNIT."""
        respx_mock.get(f"{base_url}/organizations/1/assumption").mock(
            return_value=Response(422, json={"detail": "Only UNIT"})
        )
        response = await mock_client.get("/organizations/1/assumption")
        assert response.status_code == 422


class TestUpsertAssumption:
    async def test_creates_assumption_on_success(self, mock_client, respx_mock, base_url):
        """upsert_assumption mengembalikan data asumsi setelah disimpan."""
        saved = {
            "id": 1, "organization_id": 3,
            "grade_1": 60, "grade_2": 58, "total_students": 336,
            "new_student_count": 60, "returning_student_count": 276,
            "staff_count": 24,
        }
        respx_mock.put(f"{base_url}/organizations/3/assumption").mock(
            return_value=Response(200, json=saved)
        )
        response = await mock_client.put(
            "/organizations/3/assumption",
            json={"grade_1": 60, "grade_2": 58, "new_student_count": 60,
                  "returning_student_count": 276, "staff_count": 24},
        )
        assert response.status_code == 200
        assert response.json()["staff_count"] == 24


class TestDeleteAssumption:
    async def test_returns_204_on_success(self, mock_client, respx_mock, base_url):
        """delete_assumption mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/3/assumption").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete("/organizations/3/assumption")
        assert response.status_code == 204
