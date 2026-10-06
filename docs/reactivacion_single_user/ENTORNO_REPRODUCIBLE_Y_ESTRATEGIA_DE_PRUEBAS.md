# Entorno reproducible y estrategia de pruebas

**Estado:** Python 3.12 fijado, PostgreSQL efímera y Compose verificados en CI el 2026-10-06; no certifica la suite global ni los modelos. Separar pruebas puras de pruebas con BD/ingesta/entrenamiento.

## Versiones y dependencias observadas

- CI usa Python **3.12**, Node **20**, `pip install -r backend/requirements.lock` y `npm ci` con `frontend/package-lock.json`. `requirements.txt` declara dependencias directas; `requirements.lock` fija las 51 dependencias resueltas para Python 3.12. Regenerar con `uv pip compile backend/requirements.txt --python-version 3.12 --output-file backend/requirements.lock` y probar antes de actualizar.
- Host observado 2026-10-05: Python **3.14.4**, Node **24.21.0**, npm **11.19.0**. La venv heredada `backend/.venv` apunta a Python 3.12 ausente; se verificó en venv aislada temporal de Python 3.14. No se infiere reproducibilidad de un proceso local.
- Verificar primero con Python 3.12 en una venv aislada, `<venv>/bin/python -m pip install -r backend/requirements.lock`, `cd frontend && npm ci`. No copiar una venv entre hosts ni asumir que `python3` del host es 3.12.

## Comandos seguros y gates

| Gate | Comando orientativo | Efectos / límite |
|---|---|---|
| Sintaxis Python | `python3 -m compileall -q backend` | Genera `__pycache__`; usar parseo AST si se requiere estrictamente cero escrituras. |
| Frontend lint | `cd frontend && npm run lint` | Solo lee código. |
| Frontend tests | `cd frontend && npm test` | Vitest; jsdom requiere dependencias instaladas. |
| Frontend build | `cd frontend && npm run build` | Escribe `dist/`; no despliega. |
| Backend unitarias puras | `cd backend && <venv>/python -m pytest -q <tests seleccionados>` | Examinar fixtures/side effects de cada grupo antes de correr; no usar suite global ciegamente. |
| Contratos API | `TestClient` con lifespan/BD simulados y stores temporales | El lifespan ahora solo carga artefacto local; no entrenar en pruebas ni apuntar la suite a Neon. |
| Integración BD | PostgreSQL/SQLite **efímera**, `DATABASE_URL` de test explícita y fixtures sintéticas | Prohibido apuntar a producción, escribir ingestas o entrenar modelos productivos. |

## Estrategia para la reactivación

1. Tests estáticos de rutas montadas y ausencia de dependencias comerciales; tests de `X-Usuario-Id`/Bearer no autoritativos.
2. Unitarias de configuración global, bitácora, NBA y fútbol con fixtures sintéticas y sin red.
3. Contratos FE/BE de envelope, estado, escala y errores; datos no vacíos.
4. Integración en BD efímera con snapshot sintético de varias identidades y huérfanos; validar migración sin pérdida ni mezcla.
5. E2E local con backend/frontend ligados a loopback; verificar denegación desde fuera antes de quitar auth. No usar `scripts/dev.sh` con defaults anteriores que publican `0.0.0.0`; no detener los procesos que ya están corriendo sin necesidad.
6. CI en PR/branch: lint, typecheck/build, unitarias, contratos, integración efímera, analíticas y FE; gates proporcionales, sin entrenamientos o scrapers externos.

## Estado actual conocido

La CI de la rama `reactivacion/implementacion-single-user` pasó 4/4 jobs en [run 37481234870](https://github.com/UNIVERSIDAD21/AnalyticsPredict/actions/runs/37481234870): unitarias/contratos, frontend, migración PostgreSQL efímera con dos dueños sintéticos y smoke Docker Compose con PostgreSQL desechable. Compose comprobó OpenAPI, frontend, `/salud` y puertos host en `127.0.0.1`; **no** certifica análisis funcional con base vacía. `.dockerignore` impide copiar `.env`, DB locales y caches a imágenes. `scripts/dev.sh` usa loopback por defecto, valida el intérprete y no libera puertos automáticamente. El corte analítico de solo lectura está en `RECERTIFICACION_ANALITICA_2026-10-06.md`.
