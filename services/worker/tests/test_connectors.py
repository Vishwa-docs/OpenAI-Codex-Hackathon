from services.worker.app.connectors import (
    ConnectorRequest,
    build_connector_catalog,
    sync_connector_request,
    validate_connector_request,
)


def test_connector_catalog_is_registry_driven() -> None:
    catalog = build_connector_catalog()

    assert [item.kind for item in catalog] == ["local_directory", "github", "azure_repos"]
    assert catalog[0].validation_endpoint == "/connectors/local_directory/validate"
    assert catalog[1].sync_endpoint == "/connectors/github/sync"
    assert catalog[2].project_scoped_api_key_required is True


def test_remote_connector_sync_returns_prepared_read_only_records() -> None:
    request = ConnectorRequest(
        kind="github",
        project_id="legacycart",
        repository_url="https://github.com/northstar/legacycart",
        project_api_key="proj-test-1234",
    )

    validation = validate_connector_request(request)
    assert validation.status == "ready"

    sync_response = sync_connector_request(request)
    assert sync_response.status == "prepared"
    assert sync_response.scan is not None
    assert sync_response.scan["status"] == "prepared_read_only"
    assert sync_response.scan["readOnly"] is True
    assert sync_response.scan["connectorKind"] == "github"
    assert sync_response.upstream_record is not None
    assert sync_response.upstream_record["source"]["kind"] == "git_repository"
    assert sync_response.upstream_record["connectorHandoffs"][0]["template"] == "github://owner/repo?ref=main"


def test_remote_connector_sync_is_blocked_without_credentials() -> None:
    request = ConnectorRequest(
        kind="azure_repos",
        project_id="legacycart",
        organization_url="https://dev.azure.com/northstar",
        project_name="LegacyCart",
        repository_name="legacycart",
    )

    validation = validate_connector_request(request)
    assert validation.status == "needs_credentials"

    sync_response = sync_connector_request(request)
    assert sync_response.status == "blocked"
    assert sync_response.scan is None
    assert sync_response.upstream_record is None
