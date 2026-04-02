from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from api import rutas_bitacora
from api.dependencias import obtener_usuario_id


def _app_with_router():
    app = FastAPI()
    app.include_router(rutas_bitacora.router)
    app.dependency_overrides[obtener_usuario_id] = lambda: UUID("00000000-0000-0000-0000-000000000001")
    return app


def test_auditoria_v2_403_no_admin(monkeypatch):
    app = _app_with_router()

    def _deny(_uid):
        raise HTTPException(status_code=403, detail="forbidden")

    monkeypatch.setattr(rutas_bitacora, "_exigir_admin_bitacora", _deny)
    client = TestClient(app)
    r = client.get("/api/bitacora/apuestas-analizadas/auditoria-futbol")
    assert r.status_code == 403


def test_auditoria_v2_200_admin_contract(monkeypatch):
    app = _app_with_router()
    monkeypatch.setattr(rutas_bitacora, "_exigir_admin_bitacora", lambda _uid: None)

    def _fake_obtener(**kwargs):
        assert "actualizado_desde" in kwargs
        return {
            "total": 1,
            "totales": {
                "ml": 0,
                "heuristico": 0,
                "ensemble": 1,
                "resueltas": 0,
                "no_resueltas": 1,
            },
            "promedios": {
                "edge_real": 0.03,
                "score": 70.0,
                "sizing": 0.02,
                "valor_esperado": 0.04,
                "brier_score": None,
                "log_loss": None,
                "calibration_gap": None,
                "hit_rate": None,
            },
            "cortes": [],
            "items": [],
            "filtros_aplicados": {
                "mercado": None,
                "fuente": None,
                "devig_metodo": None,
                "creado_desde": None,
                "creado_hasta": None,
                "actualizado_desde": None,
                "actualizado_hasta": None,
                "fecha_partido_desde": None,
                "fecha_partido_hasta": None,
                "partido_id": None,
                "modelo_version_id": None,
                "calibrador_id": None,
                "estado": None,
                "resultado_outcome": None,
            },
            "paginacion": {"limite": 200, "offset": 0, "items": 0},
        }

    import servicios.apuestas_analizadas as svc

    monkeypatch.setattr(svc, "obtener_auditoria_decisiones_futbol", _fake_obtener)
    client = TestClient(app)
    r = client.get("/api/bitacora/apuestas-analizadas/auditoria-futbol")
    assert r.status_code == 200
    body = r.json()
    assert body["exito"] is True
    assert body["totales"]["ensemble"] == 1


def test_auditoria_legacy_200(monkeypatch):
    app = _app_with_router()
    monkeypatch.setattr(rutas_bitacora, "_exigir_admin_bitacora", lambda _uid: None)
    import servicios.apuestas_analizadas as svc

    monkeypatch.setattr(
        svc,
        "obtener_auditoria_decisiones_futbol",
        lambda **kwargs: {
            "total": 0,
            "totales": {"ml": 0, "heuristico": 0, "ensemble": 0, "resueltas": 0, "no_resueltas": 0},
            "promedios": {"edge_real": None, "score": None, "sizing": None, "valor_esperado": None, "brier_score": None, "log_loss": None, "calibration_gap": None, "hit_rate": None},
            "cortes": [],
            "items": [],
            "filtros_aplicados": {},
            "paginacion": {"limite": 200, "offset": 0, "items": 0},
        },
    )
    client = TestClient(app)
    r = client.get("/api/bitacora/apuestas-analizadas/auditoria-futbol/legacy")
    assert r.status_code == 200


def test_backfill_endpoint_calls_service(monkeypatch):
    app = _app_with_router()
    monkeypatch.setattr(rutas_bitacora, "_exigir_admin_bitacora", lambda _uid: None)
    import servicios.apuestas_analizadas as svc

    monkeypatch.setattr(
        svc,
        "backfill_decisiones_desde_payload_futbol",
        lambda **kwargs: {"dry_run": kwargs.get("dry_run"), "candidatas": 2, "actualizadas": 0},
    )
    client = TestClient(app)
    r = client.post("/api/bitacora/apuestas-analizadas/auditoria-futbol/backfill?dry_run=true")
    assert r.status_code == 200
    assert r.json()["dry_run"] is True
