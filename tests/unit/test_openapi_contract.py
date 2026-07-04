from emergencypulse.main import app


def test_openapi_schema_contains_required_api_paths() -> None:
    schema = app.openapi()

    assert schema["openapi"] == "3.0.3"
    assert "/healthz" in schema["paths"]
    assert "/readyz" in schema["paths"]
    assert "/api/v1/auth/token" in schema["paths"]
    assert "/api/v1/dispatch/incidents" in schema["paths"]
    assert "/api/v1/routes/best" in schema["paths"]


def test_dispatch_endpoint_documents_bearer_auth_and_examples() -> None:
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/dispatch/incidents"]["post"]

    assert operation["security"] == [{"OAuth2PasswordBearer": ["dispatch:write"]}]
    assert "examples" in operation["requestBody"]["content"]["application/json"]
    assert "201" in operation["responses"]
    assert "409" in operation["responses"]


def test_public_route_endpoint_is_documented_without_auth() -> None:
    schema = app.openapi()
    operation = schema["paths"]["/api/v1/routes/best"]["post"]

    assert "security" not in operation
    assert "examples" in operation["requestBody"]["content"]["application/json"]
    assert operation["tags"] == ["routes"]
    assert "200" in operation["responses"]
