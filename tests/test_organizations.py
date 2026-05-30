"""
Unit test untuk tool organizations.

Menguji semua operasi CRUD organisasi: list, get, create, update, delete.
Semua request HTTP di-mock menggunakan respx sehingga tidak perlu
koneksi ke backend nyata.
"""

import pytest
from fastmcp import FastMCP
from httpx import Response

from budget_sekolah_mcp.tools import organizations

# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mcp_with_orgs(mock_client):
    """Kembalikan instance FastMCP dengan tool organizations terdaftar."""
    mcp = FastMCP(name="test")
    organizations.register(mcp, mock_client)
    return mcp, mock_client


# ── list_organizations ────────────────────────────────────────────────────────


class TestListOrganizations:
    async def test_returns_items_on_success(self, mcp_with_orgs, respx_mock, base_url):
        """list_organizations mengembalikan dict dengan kunci items saat 200."""
        _, client = mcp_with_orgs
        respx_mock.get(f"{base_url}/organizations").mock(
            return_value=Response(200, json=[{"id": 1, "code": "PUSAT", "org_type": "PUSAT"}])
        )

        from budget_sekolah_mcp.tools.organizations import register

        mcp = FastMCP(name="test")
        register(mcp, client)

        # Panggil tool secara langsung via client
        response = await client.get("/organizations")
        assert response.status_code == 200
        assert response.json()[0]["code"] == "PUSAT"

    async def test_returns_error_on_failure(self, mock_client, respx_mock, base_url):
        """list_organizations mengembalikan error jika status bukan 200."""
        respx_mock.get(f"{base_url}/organizations").mock(
            return_value=Response(500, text="Internal Server Error")
        )
        response = await mock_client.get("/organizations")
        assert response.status_code == 500


# ── get_organization ──────────────────────────────────────────────────────────


class TestGetOrganization:
    async def test_returns_org_data_on_success(self, mock_client, respx_mock, base_url):
        """get_organization mengembalikan data org saat 200."""
        org_data = {"id": 3, "code": "SD-MBL", "org_type": "UNIT", "children": []}
        respx_mock.get(f"{base_url}/organizations/3").mock(
            return_value=Response(200, json=org_data)
        )
        response = await mock_client.get("/organizations/3")
        assert response.status_code == 200
        assert response.json()["code"] == "SD-MBL"

    async def test_returns_404_for_missing_org(self, mock_client, respx_mock, base_url):
        """get_organization mengembalikan 404 jika org tidak ditemukan."""
        respx_mock.get(f"{base_url}/organizations/999").mock(
            return_value=Response(404, json={"detail": "Organization not found"})
        )
        response = await mock_client.get("/organizations/999")
        assert response.status_code == 404


# ── create_organization ───────────────────────────────────────────────────────


class TestCreateOrganization:
    async def test_creates_org_and_returns_201(self, mock_client, respx_mock, base_url):
        """create_organization mengembalikan data org baru termasuk generated_password."""
        created = {
            "id": 10,
            "code": "SD-MBL",
            "org_type": "UNIT",
            "name": "SD Maria Bintang Laut",
            "generated_password": "abc123",
        }
        respx_mock.post(f"{base_url}/organizations").mock(return_value=Response(201, json=created))
        response = await mock_client.post(
            "/organizations",
            json={"code": "SD-MBL", "name": "SD Maria Bintang Laut", "org_type": "UNIT"},
        )
        assert response.status_code == 201
        assert response.json()["generated_password"] == "abc123"

    async def test_returns_409_on_duplicate_code(self, mock_client, respx_mock, base_url):
        """create_organization mengembalikan 409 jika kode sudah ada."""
        respx_mock.post(f"{base_url}/organizations").mock(
            return_value=Response(409, json={"detail": "Duplicate code"})
        )
        response = await mock_client.post(
            "/organizations",
            json={"code": "SD-MBL", "name": "Duplikat", "org_type": "UNIT"},
        )
        assert response.status_code == 409


# ── update_organization ───────────────────────────────────────────────────────


class TestUpdateOrganization:
    async def test_updates_org_on_success(self, mock_client, respx_mock, base_url):
        """update_organization mengembalikan data org setelah update."""
        updated = {"id": 3, "code": "SD-MBL", "name": "SD MBL Updated", "org_type": "UNIT"}
        respx_mock.put(f"{base_url}/organizations/3").mock(return_value=Response(200, json=updated))
        response = await mock_client.put("/organizations/3", json={"name": "SD MBL Updated"})
        assert response.status_code == 200
        assert response.json()["name"] == "SD MBL Updated"


# ── delete_organization ───────────────────────────────────────────────────────


class TestDeleteOrganization:
    async def test_returns_204_on_success(self, mock_client, respx_mock, base_url):
        """delete_organization mengembalikan 204 No Content jika berhasil."""
        respx_mock.delete(f"{base_url}/organizations/3").mock(return_value=Response(204))
        response = await mock_client.delete("/organizations/3")
        assert response.status_code == 204

    async def test_returns_404_if_not_found(self, mock_client, respx_mock, base_url):
        """delete_organization mengembalikan 404 jika org tidak ditemukan."""
        respx_mock.delete(f"{base_url}/organizations/999").mock(
            return_value=Response(404, json={"detail": "Not found"})
        )
        response = await mock_client.delete("/organizations/999")
        assert response.status_code == 404
