"""Test per la gestione errori globale dell'app (404, redirect, ecc.)."""
from fastapi.testclient import TestClient


def test_404_on_public_page_returns_html_not_json(client: TestClient):
    """Una pagina pubblica inesistente deve mostrare una pagina HTML, non JSON grezzo."""
    response = client.get("/pagina-che-non-esiste")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "Torna alla home" in response.text


def test_404_on_api_path_still_returns_json(client: TestClient):
    """Le route /api/ devono continuare a rispondere in JSON."""
    response = client.get("/api/percorso-inesistente")
    assert response.status_code == 404
    assert "application/json" in response.headers["content-type"]


def test_unauthenticated_admin_redirects_to_login(client: TestClient):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code in (302, 303)
    assert "/admin/login" in response.headers["location"]
