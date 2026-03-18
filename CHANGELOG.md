# CHANGELOG

## 2026-03-18
- Se incorporó al repositorio el plan de ejecución por bloques v3 en `docs/arquitectura/PLAN_EJECUCION_BLOQUES_V3.md`.
- Se creó `docs/arquitectura/ESTADO_PROYECTO.md` como fuente única de estado operativo por bloque.
- Se agregaron ADRs iniciales:
  - `ADR-001-auth.md` (JWT + refresh + reset)
  - `ADR-002-pagos.md` (MercadoPago por foco LATAM + nota Stripe para Europa)
  - `ADR-003-chat-contexto.md` (ventana deslizante N para controlar costo LLM)
- Se inició limpieza de documentación obsoleta para evitar uso de contexto duplicado.
- Se agregó CI básico en GitHub Actions (`.github/workflows/ci.yml`) con:
  - backend smoke tests (`pytest -q tests/test_smoke_api.py`)
  - frontend lint + build (`npm run lint`, `npm run build`)
- Se creó base de staging en Docker:
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `deploy/staging/docker-compose.yml`
  - `deploy/staging/staging.env.example`
