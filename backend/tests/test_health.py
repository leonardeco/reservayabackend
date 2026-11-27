from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.deps import get_db
from app.main import create_app


def test_health_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_db_caida_responde_503():
    class SesionRota:
        def execute(self, *_args, **_kwargs):
            raise OperationalError("SELECT 1", {}, Exception("db caída"))

        def close(self):
            pass

    app = create_app()
    app.dependency_overrides[get_db] = lambda: SesionRota()
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "error", "db": "unavailable"}}


def test_openapi_bajo_prefijo(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "ReservaYa API"
