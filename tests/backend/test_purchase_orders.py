"""
Tests for purchase order API endpoints.
"""
import pytest

import mock_data


@pytest.fixture(autouse=True)
def reset_purchase_orders():
    """Keep tests independent.

    POST /api/purchase-orders appends to the module-level list loaded at import
    time, so without this every created order would leak into the next test.
    """
    original = list(mock_data.purchase_orders)
    yield
    mock_data.purchase_orders[:] = original


@pytest.fixture
def backlog_item_id(client):
    """ID of the first backlog item, used as a valid PO target."""
    response = client.get("/api/backlog")
    assert response.status_code == 200

    backlog = response.json()
    assert len(backlog) > 0
    return backlog[0]["id"]


def build_request(backlog_item_id, **overrides):
    """Valid create-PO payload, with per-test overrides."""
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "FilterMax Inc",
        "quantity": 350,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-10-15",
        "notes": "Rush order",
    }
    payload.update(overrides)
    return payload


class TestPurchaseOrderEndpoints:
    """Test suite for purchase-order-related endpoints."""

    def test_get_all_purchase_orders(self, client):
        """Test getting all purchase orders."""
        response = client.get("/api/purchase-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_purchase_order(self, client, backlog_item_id):
        """Test creating a purchase order against a backlog item."""
        response = client.post(
            "/api/purchase-orders", json=build_request(backlog_item_id)
        )
        assert response.status_code == 201

        purchase_order = response.json()
        assert purchase_order["backlog_item_id"] == backlog_item_id
        assert purchase_order["supplier_name"] == "FilterMax Inc"
        assert purchase_order["quantity"] == 350
        assert purchase_order["unit_cost"] == 12.5
        assert purchase_order["expected_delivery_date"] == "2025-10-15"
        assert purchase_order["notes"] == "Rush order"

    def test_created_purchase_order_structure(self, client, backlog_item_id):
        """Test that a created purchase order has the full expected structure."""
        response = client.post(
            "/api/purchase-orders", json=build_request(backlog_item_id)
        )
        purchase_order = response.json()

        for field in [
            "id",
            "backlog_item_id",
            "supplier_name",
            "quantity",
            "unit_cost",
            "expected_delivery_date",
            "status",
            "created_date",
            "notes",
        ]:
            assert field in purchase_order

        assert isinstance(purchase_order["quantity"], int)
        assert isinstance(purchase_order["unit_cost"], (int, float))
        assert purchase_order["status"] == "pending"

    def test_create_purchase_order_without_notes(self, client, backlog_item_id):
        """Test that notes are optional when creating a purchase order."""
        payload = build_request(backlog_item_id)
        del payload["notes"]

        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_created_purchase_order_appears_in_list(self, client, backlog_item_id):
        """Test that a created purchase order is returned by the list endpoint."""
        created = client.post(
            "/api/purchase-orders", json=build_request(backlog_item_id)
        ).json()

        response = client.get("/api/purchase-orders")
        assert response.status_code == 200

        ids = [purchase_order["id"] for purchase_order in response.json()]
        assert created["id"] in ids

    def test_create_purchase_order_for_nonexistent_backlog_item(self, client):
        """Test creating a purchase order for a backlog item that doesn't exist."""
        response = client.post(
            "/api/purchase-orders", json=build_request("nonexistent-backlog-999")
        )
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_create_duplicate_purchase_order(self, client, backlog_item_id):
        """Test that a backlog item can only have one purchase order."""
        first = client.post("/api/purchase-orders", json=build_request(backlog_item_id))
        assert first.status_code == 201

        second = client.post("/api/purchase-orders", json=build_request(backlog_item_id))
        assert second.status_code == 409

        data = second.json()
        assert "detail" in data
        assert "already has a purchase order" in data["detail"].lower()

    def test_create_purchase_order_rejects_zero_quantity(self, client, backlog_item_id):
        """Test that a purchase order must have a positive quantity."""
        response = client.post(
            "/api/purchase-orders", json=build_request(backlog_item_id, quantity=0)
        )
        assert response.status_code == 422

    def test_create_purchase_order_rejects_negative_unit_cost(
        self, client, backlog_item_id
    ):
        """Test that a purchase order cannot have a negative unit cost."""
        response = client.post(
            "/api/purchase-orders", json=build_request(backlog_item_id, unit_cost=-1.0)
        )
        assert response.status_code == 422

    def test_create_purchase_order_requires_supplier_name(
        self, client, backlog_item_id
    ):
        """Test that supplier_name is a required field."""
        payload = build_request(backlog_item_id)
        del payload["supplier_name"]

        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 422


class TestBacklogPurchaseOrderLink:
    """Test suite for how backlog items expose their purchase order."""

    def test_backlog_items_without_purchase_order(self, client):
        """Test that backlog items start with no purchase order attached."""
        response = client.get("/api/backlog")
        assert response.status_code == 200

        for item in response.json():
            assert item["has_purchase_order"] is False
            assert item["purchase_order_id"] is None
            assert item["purchase_order"] is None

    def test_backlog_item_links_to_created_purchase_order(
        self, client, backlog_item_id
    ):
        """Test that creating a purchase order links it onto the backlog item."""
        created = client.post(
            "/api/purchase-orders", json=build_request(backlog_item_id)
        ).json()

        response = client.get("/api/backlog")
        assert response.status_code == 200

        item = next(i for i in response.json() if i["id"] == backlog_item_id)
        assert item["has_purchase_order"] is True
        assert item["purchase_order_id"] == created["id"]
        assert item["purchase_order"]["supplier_name"] == "FilterMax Inc"

    def test_other_backlog_items_are_unaffected(self, client, backlog_item_id):
        """Test that a purchase order only links to its own backlog item."""
        client.post("/api/purchase-orders", json=build_request(backlog_item_id))

        response = client.get("/api/backlog")
        others = [i for i in response.json() if i["id"] != backlog_item_id]

        for item in others:
            assert item["has_purchase_order"] is False
            assert item["purchase_order_id"] is None
