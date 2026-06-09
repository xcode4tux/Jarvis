"""Tests for the /v1/connectors API router."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def app():
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi not installed")

    from openjarvis.server.connectors_router import create_connectors_router

    _app = FastAPI()
    router = create_connectors_router()
    # The router already carries ``prefix="/v1/connectors"``. The real
    # ``server/app.py`` mounts it with ``include_router(router)`` — adding
    # a second ``prefix="/v1"`` here would produce ``/v1/v1/connectors``
    # and every request would 404.
    _app.include_router(router)
    return TestClient(_app)


def test_list_connectors(app):
    """GET /v1/connectors returns a list that includes the obsidian connector."""
    resp = app.get("/v1/connectors")
    assert resp.status_code == 200
    data = resp.json()
    assert "connectors" in data
    ids = [c["connector_id"] for c in data["connectors"]]
    assert "obsidian" in ids


def test_connector_detail(app):
    """GET /v1/connectors/obsidian returns the expected fields."""
    resp = app.get("/v1/connectors/obsidian")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connector_id"] == "obsidian"
    assert "display_name" in data
    assert "auth_type" in data
    assert "connected" in data
    assert "mcp_tools" in data


def test_connector_not_found(app):
    """GET /v1/connectors/nonexistent returns 404."""
    resp = app.get("/v1/connectors/nonexistent")
    assert resp.status_code == 404


def test_connect_obsidian(app, tmp_path):
    """POST /v1/connectors/obsidian/connect with a valid path marks it connected."""
    # Create a minimal vault directory so is_connected() returns True.
    vault = tmp_path / "vault"
    vault.mkdir()

    resp = app.post("/v1/connectors/obsidian/connect", json={"path": str(vault)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["connector_id"] == "obsidian"
    assert data["connected"] is True


def test_disconnect(app):
    """POST /v1/connectors/obsidian/disconnect returns 200 with connected=False."""
    resp = app.post("/v1/connectors/obsidian/disconnect")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connector_id"] == "obsidian"
    assert data["connected"] is False


def test_sync_status(app):
    """GET /v1/connectors/obsidian/sync returns a response with a state field."""
    resp = app.get("/v1/connectors/obsidian/sync")
    assert resp.status_code == 200
    data = resp.json()
    assert "state" in data
    assert data["connector_id"] == "obsidian"


def test_trigger_sync(app, tmp_path: Path) -> None:
    """POST /v1/connectors/obsidian/sync triggers an incremental sync.

    The endpoint is intentionally fire-and-forget — it starts the sync in
    a background thread and returns immediately with ``status=started``.
    Sync progress is observable via the separate ``GET .../sync`` endpoint.
    """
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("# Test note\n\nContent here.")
    app.post("/v1/connectors/obsidian/connect", json={"path": str(vault)})
    resp = app.post("/v1/connectors/obsidian/sync")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connector_id"] == "obsidian"
    assert data["status"] in {"started", "already_syncing"}


# ---------------------------------------------------------------------------
# Connect-time credential validation (GH #409): the /connect endpoint must
# reject invalid credentials with HTTP 400 and never persist (or overwrite)
# anything on disk when validation fails.
# ---------------------------------------------------------------------------


def test_connect_slack_bot_token_returns_400(app, tmp_path: Path) -> None:
    """POST connect with an xoxb- token is rejected 400 and writes nothing."""
    from openjarvis.connectors.slack_connector import SlackConnector
    from openjarvis.server.connectors_router import _instances

    creds = tmp_path / "slack.json"
    _instances["slack"] = SlackConnector(credentials_path=str(creds))
    try:
        resp = app.post(
            "/v1/connectors/slack/connect", json={"token": "xoxb-fake-token"}
        )
        assert resp.status_code == 400
        assert "xoxb" in resp.json()["detail"].lower()
        assert not creds.exists()
    finally:
        _instances.pop("slack", None)


def test_connect_granola_invalid_key_returns_400_keeps_existing(
    app, tmp_path: Path
) -> None:
    """A bad Granola key is rejected 400 and the existing credential survives."""
    import json
    from unittest.mock import patch

    from openjarvis.connectors.granola import GranolaConnector, GranolaKeyError
    from openjarvis.server.connectors_router import _instances

    creds = tmp_path / "granola.json"
    creds.write_text(json.dumps({"token": "grl_real_existing_key"}))
    _instances["granola"] = GranolaConnector(credentials_path=str(creds))
    try:
        with patch(
            "openjarvis.connectors.granola._granola_api_validate_key",
            side_effect=GranolaKeyError(
                "Invalid API key. Check your key in Granola Settings → API."
            ),
        ):
            resp = app.post(
                "/v1/connectors/granola/connect",
                json={"code": "fake-key-12345"},
            )
        assert resp.status_code == 400
        assert "Invalid API key" in resp.json()["detail"]
        # The previously-working credential must be untouched.
        assert json.loads(creds.read_text())["token"] == "grl_real_existing_key"
    finally:
        _instances.pop("granola", None)


class TestCustomConnectorsEndpoints:
    def test_custom_connector_lifecycle(self, app, tmp_path: Path) -> None:
        from unittest.mock import patch
        from openjarvis.core.registry import ConnectorRegistry

        # Patch DEFAULT_CONFIG_DIR to isolated test temp path
        with patch("openjarvis.core.config.DEFAULT_CONFIG_DIR", tmp_path):
            
            # 1. Add custom filesystem connector
            add_resp = app.post(
                "/v1/connectors/custom",
                json={
                    "connector_id": "test_custom_fs",
                    "display_name": "Test Custom Folder",
                    "auth_type": "filesystem",
                    "description": "My custom folder",
                }
            )
            assert add_resp.status_code == 200
            assert add_resp.json()["status"] == "success"
            assert add_resp.json()["connector_id"] == "test_custom_fs"

            # Verify it is registered in Registry
            assert ConnectorRegistry.contains("test_custom_fs")

            # 2. List connectors and verify custom is listed
            list_resp = app.get("/v1/connectors")
            assert list_resp.status_code == 200
            connectors = list_resp.json()["connectors"]
            custom_entry = next((c for c in connectors if c["connector_id"] == "test_custom_fs"), None)
            assert custom_entry is not None
            assert custom_entry["display_name"] == "Test Custom Folder"
            assert custom_entry["auth_type"] == "filesystem"
            assert custom_entry["is_custom"] is True
            assert custom_entry["description"] == "My custom folder"
            assert custom_entry["connected"] is False

            # 3. Connect the custom connector (create a path to vault)
            vault_dir = tmp_path / "custom_vault"
            vault_dir.mkdir()
            (vault_dir / "note.txt").write_text("Hello Custom Source!")

            conn_resp = app.post(
                "/v1/connectors/test_custom_fs/connect",
                json={"path": str(vault_dir)}
            )
            assert conn_resp.status_code == 200
            assert conn_resp.json()["connected"] is True

            # Verify it is connected in detail route
            detail_resp = app.get("/v1/connectors/test_custom_fs")
            assert detail_resp.status_code == 200
            assert detail_resp.json()["connected"] is True

            # 4. Trigger sync (creates background thread)
            sync_resp = app.post("/v1/connectors/test_custom_fs/sync")
            assert sync_resp.status_code == 200
            assert sync_resp.json()["status"] in {"started", "already_syncing"}

            # 5. Delete custom connector
            del_resp = app.delete("/v1/connectors/custom/test_custom_fs")
            assert del_resp.status_code == 200
            assert del_resp.json()["status"] == "success"

            # Verify deleted from registry
            assert not ConnectorRegistry.contains("test_custom_fs")

