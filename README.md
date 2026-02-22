# AnalyticsPredict

Proyecto de análisis deportivo con:
- **Backend** en FastAPI
- **Frontend** en React + Vite

## Requisitos

- Python 3.10+
- Node.js 18+
- npm 9+

## Estructura

- `backend/` API FastAPI
- `frontend/` interfaz web React
- `scripts/dev.sh` arranque conjunto backend+frontend

## Arranque rápido (recomendado)

Desde root del repo:

```bash
chmod +x scripts/dev.sh
bash scripts/dev.sh
```

Esto levanta:
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

`dev.sh` libera automáticamente los puertos `8000` y `5173` antes de iniciar.
Si no quieres ese comportamiento:

```bash
AUTO_KILL_PORTS=false bash scripts/dev.sh
```

## Arranque manual

### Backend (con venv recomendado)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Backend (sin venv, bajo tu responsabilidad)

```bash
cd backend
python3 -m pip install --break-system-packages -r requirements.txt
python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Comandos útiles

Desde root:

```bash
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

1. Copia variables de entorno:

```bash
cp .env.example .env
```

2. Ajusta `.env` según tu entorno (DB, puertos, etc.).

## Tests rápidos (Smoke)

Desde `backend/`:

```bash
pytest -q tests/test_smoke_api.py
```

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
