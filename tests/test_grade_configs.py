"""
Unit test untuk tool grade_configs.

Menguji operasi get, upsert, dan delete konfigurasi grade untuk organisasi UNIT.
"""

from httpx import Response


class TestGetGradeConfig:
    async def test_returns_config_on_success(self, mock_client, respx_mock, base_url):
        """get_grade_config mengembalikan data konfigurasi saat 200."""
        config_data = {
            "id": 1,
            "organization_id": 3,
            "num_grades": 3,
            "grade_1_label": "TK A",
            "active_grades": [{"slot": 1, "label": "TK A"}],
        }
        respx_mock.get(f"{base_url}/organizations/3/grade-config").mock(
            return_value=Response(200, json=config_data)
        )
        response = await mock_client.get("/organizations/3/grade-config")
        assert response.status_code == 200
        assert response.json()["num_grades"] == 3

    async def test_returns_404_if_not_set(self, mock_client, respx_mock, base_url):
        """get_grade_config mengembalikan 404 jika konfigurasi belum diisi."""
        respx_mock.get(f"{base_url}/organizations/3/grade-config").mock(
            return_value=Response(404, json={"detail": "Konfigurasi grade belum diisi"})
        )
        response = await mock_client.get("/organizations/3/grade-config")
        assert response.status_code == 404

    async def test_returns_422_for_non_unit(self, mock_client, respx_mock, base_url):
        """get_grade_config mengembalikan 422 jika org bukan UNIT."""
        respx_mock.get(f"{base_url}/organizations/1/grade-config").mock(
            return_value=Response(422, json={"detail": "Only UNIT"})
        )
        response = await mock_client.get("/organizations/1/grade-config")
        assert response.status_code == 422


class TestUpsertGradeConfig:
    async def test_saves_config_on_success(self, mock_client, respx_mock, base_url):
        """upsert_grade_config mengembalikan data konfigurasi setelah disimpan."""
        saved = {
            "id": 1,
            "organization_id": 3,
            "num_grades": 3,
            "grade_1_label": "TK A",
            "grade_2_label": "TK B",
            "grade_3_label": "TK C",
            "active_grades": [
                {"slot": 1, "label": "TK A"},
                {"slot": 2, "label": "TK B"},
                {"slot": 3, "label": "TK C"},
            ],
        }
        respx_mock.put(f"{base_url}/organizations/3/grade-config").mock(
            return_value=Response(200, json=saved)
        )
        response = await mock_client.put(
            "/organizations/3/grade-config",
            json={
                "num_grades": 3,
                "grade_1_label": "TK A",
                "grade_2_label": "TK B",
                "grade_3_label": "TK C",
            },
        )
        assert response.status_code == 200
        assert len(response.json()["active_grades"]) == 3

    async def test_returns_422_for_label_out_of_range(self, mock_client, respx_mock, base_url):
        """upsert_grade_config mengembalikan 422 jika label di luar num_grades."""
        respx_mock.put(f"{base_url}/organizations/3/grade-config").mock(
            return_value=Response(422, json={"detail": "grade_4_label harus None"})
        )
        response = await mock_client.put(
            "/organizations/3/grade-config",
            json={"num_grades": 3, "grade_4_label": "X"},
        )
        assert response.status_code == 422


class TestDeleteGradeConfig:
    async def test_returns_204_on_success(self, mock_client, respx_mock, base_url):
        """delete_grade_config mengembalikan 204 jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/3/grade-config").mock(
            return_value=Response(204)
        )
        response = await mock_client.delete("/organizations/3/grade-config")
        assert response.status_code == 204
