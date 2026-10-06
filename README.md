# AnalyticsPredict

> Herramienta privada personal single-user desde el corte del 2026-10-05: sin login, pagos, suscripciones ni tiers en API/UI activos. El trabajo de confiabilidad y recertificación analítica continúa; ver `docs/reactivacion_single_user/`. No exponer la API sin protección de infraestructura.

Proyecto de análisis deportivo con:
- **Backend** en FastAPI
- **Frontend** en React + Vite

## Requisitos

- Python 3.12 (versión de CI; 3.14 verificada en pruebas dirigidas)
- Node.js 20 (versión de CI)
- npm y `frontend/package-lock.json`
- PostgreSQL configurado mediante `backend/.env` con `DATABASE_URL` protegida. No apuntar pruebas de integración a Neon.

## Estructura

- `backend/` API FastAPI
- `frontend/` interfaz web React
- `scripts/dev.sh` arranque conjunto backend+frontend

## Arranque rápido (recomendado)

Desde root del repo:

```bash
bash scripts/dev.sh
```

Esto levanta:
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

`dev.sh` usa `127.0.0.1` y no detiene procesos existentes por defecto.
Requiere `backend/.venv` válido o `BACKEND_PYTHON` con dependencias instaladas; valida el intérprete antes de arrancar. La aplicación puede consultar BD y entrenar al iniciar: no usar el arranque como prueba inocua.
Para liberar puertos existentes de forma explícita:

```bash
AUTO_KILL_PORTS=true bash scripts/dev.sh
```

## Arranque manual

### Backend (con venv recomendado)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

## Comandos útiles

Desde root:

```bash
make help
make dev
make backend
make frontend
make calidad-ciclo
make calidad-ciclo-fast
make reporte-ejecutivo
make qa-preflight
make reporte-semanal-template
make reporte-semanal-auto
make export-metricas-csv
make snapshot-tendencias
make revision-politica
make check-modo-estricto
make cierre-operativo
make estado-unificado
make operacion-diaria-full
```

`make calidad-ciclo` ejecuta resolución (baloncesto + fútbol), captura tablero de salud y ranking de mercados, y guarda evidencias en `reports/calidad/<timestamp>/`.
`make reporte-ejecutivo` genera un reporte directivo con acciones priorizadas.
`make reporte-semanal-auto` genera reporte semanal completo con drift, mercados críticos y acciones.
`make export-metricas-csv` exporta CSV listos para BI/análisis externo.
`make revision-politica` genera revisión de policy y umbrales sugeridos.
`make qa-preflight` valida compilación y endpoints críticos.

## Configuración

1. Copia el ejemplo privado de backend:

```bash
cp backend/.env.example backend/.env
```

2. Configura `DATABASE_URL` en `backend/.env` mediante el mecanismo protegido del entorno. No publiques ese archivo.

## Pruebas dirigidas sin BD

Desde la raíz, con la venv backend activa:

```bash
cd backend
python -m pytest -q tests/test_metricas_1x2_futbol.py tests/test_rutas_bitacora_payload.py tests/api/test_bitacora_contract.py tests/api/test_apuestas_futbol_contract.py tests/api/test_single_user_contract.py tests/test_smoke_api.py
cd ../frontend
npm test && npm run lint && npm run build
```

Estas pruebas no certifican la suite global ni la BD; la estrategia para integración aislada está en `docs/reactivacion_single_user/ENTORNO_REPRODUCIBLE_Y_ESTRATEGIA_DE_PRUEBAS.md`.

Checklist local:
- `docs/CHECKLIST_VALIDACION_LOCAL.md`

## Documentación

- API Swagger: `http://localhost:8000/docs`
- API ReDoc: `http://localhost:8000/redoc`
- Contrato API: `docs/CONTRATO_API_PROFESIONAL.md`
- Resumen operativo por deporte: `GET /api/metricas/resumen-deportes`
- Tablero profesional: `GET /api/metricas/tablero-salud`
- Ranking por mercado: `GET /api/metricas/calidad-mercados`
- Plan automático de acción: `GET /api/metricas/recomendaciones-accion`
- Drift por mercado: `GET /api/metricas/drift-mercados`
- Política de bloqueo de mercados: `GET /api/metricas/politica-mercados`
- Alertas de ingestión stale: `GET /api/metricas/alertas-ingestion`
- Sugerencias de umbrales automáticos: `GET /api/metricas/sugerencias-umbrales`
- Gate global producción estricta: `GET /api/metricas/modo-estricto` (GO/NO-GO)
- Resumen ejecutivo 30s: `GET /api/metricas/resumen-ejecutivo-compacto`

## Operative check
- Updated by Borlty on 2026-03-01 to validate commit/push pipeline.
