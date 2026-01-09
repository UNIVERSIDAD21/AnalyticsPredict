# Analizador NBA - Backend (Fase 1)

Backend para análisis de apuestas deportivas NBA con predicciones por cuarto y juego completo.

## Requisitos

- Python 3.10+
- `pip`

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

## Configuración

Copia `.env.example` a `.env` y ajusta valores si es necesario.

## Ejecutar servidor

```bash
cd backend
uvicorn app:app --reload --port 8000
```

## Documentación

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints principales

- `GET /` Información del servidor
- `GET /salud` Health check
- `GET /api/equipos` Listado de equipos
- `POST /api/analizar` Análisis de partido
- `POST /api/analizar-en-vivo` Análisis con cuartos reales

## Documentación Profesional

Para documentación completa del contrato de API, incluyendo:
- Campos de request/response
- Reglas de precedencia
- Ejemplos narrativos por escenario
- Códigos de advertencia

Ver: [docs/CONTRATO_API_PROFESIONAL.md](docs/CONTRATO_API_PROFESIONAL.md)
