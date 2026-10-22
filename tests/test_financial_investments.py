"""
Unit test untuk tool financial_investments (investasi keuangan, baca-saja).

Memanggil tool ``list_financial_investments`` yang benar-benar terdaftar pada
instance FastMCP, dengan backend di-mock oleh respx.
"""

import pytest
from fastmcp import Client, FastMCP
from httpx import Response

from budget_sekolah_mcp.tools import financial_investments

ROW = {
    "id": 1,
    "organization_id": 1,
    "instrument_type": "DEPOSITO",
    "name": "Deposito Bank",
    "amount": 2000000000,
    "notes": None,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00",
}


@pytest.fixture
def tool_server(mock_client):
    """FastMCP berisi tool financial_investments memakai mock_client."""
    mcp = FastMCP("test")
    financial_investments.register(mcp, mock_client)
    return mcp


async def _call(server, org_id=1):
    async with Client(server) as c:
        result = await c.call_tool("list_financial_investments", {"org_id": org_id})
        return result.data


class TestListFinancialInvestments:
    async def test_only_org_id_parameter(self, tool_server):
        """Tool hanya menerima org_id."""
        async with Client(tool_server) as c:
            tools = {t.name: t for t in await c.list_tools()}
        assert list(tools["list_financial_investments"].inputSchema["properties"]) == ["org_id"]
        assert not any(
            n.startswith(("create_financial", "update_financial", "delete_financial"))
            for n in tools
        )

    async def test_returns_items(self, tool_server, respx_mock, base_url):
        """200 berisi baris -> items apa adanya."""
        respx_mock.get(f"{base_url}/organizations/1/financial-investments").mock(
            return_value=Response(200, json=[ROW])
        )
        data = await _call(tool_server)
        assert data["items"][0]["amount"] == 2000000000
        assert data["items"][0]["instrument_type"] == "DEPOSITO"

    async def test_returns_empty(self, tool_server, respx_mock, base_url):
        """200 [] -> items kosong."""
        respx_mock.get(f"{base_url}/organizations/1/financial-investments").mock(
            return_value=Response(200, json=[])
        )
        assert await _call(tool_server) == {"items": []}

    async def test_404(self, tool_server, respx_mock, base_url):
        """404 -> error Organization not found."""
        respx_mock.get(f"{base_url}/organizations/1/financial-investments").mock(
            return_value=Response(404, json={"detail": "x"})
        )
        data = await _call(tool_server)
        assert data["error"] == "Organization not found"
        assert data["org_id"] == 1

    async def test_403(self, tool_server, respx_mock, base_url):
        """403 -> error dengan status_code."""
        respx_mock.get(f"{base_url}/organizations/1/financial-investments").mock(
            return_value=Response(403, text="Akses ditolak")
        )
        data = await _call(tool_server)
        assert data["status_code"] == 403
        assert "error" in data
