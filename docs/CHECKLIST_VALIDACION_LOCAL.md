# Checklist de validación local (Backend + Frontend)

## 1) Arranque

- [ ] `bash scripts/dev.sh` levanta ambos servicios sin errores fatales.
- [ ] Backend accesible en `http://localhost:8000`.
- [ ] Frontend accesible en `http://localhost:5173`.

## 2) API básica (smoke)

- [ ] `GET /` responde 200.
- [ ] `GET /salud` responde 200.
- [ ] `GET /api/modelo/estado` responde 200 (exito true/false según datos disponibles).

## 3) Ejecución de tests

Desde `backend/`:

```bash
pytest -q tests/test_smoke_api.py
```

Validación esperada:
- [ ] 3 tests passed.

## 4) Verificación visual

- [ ] Swagger abre en `http://localhost:8000/docs`.
- [ ] Frontend carga sin pantalla en blanco.

## 5) Cierre limpio

- [ ] `Ctrl+C` en `scripts/dev.sh` detiene backend y frontend.
