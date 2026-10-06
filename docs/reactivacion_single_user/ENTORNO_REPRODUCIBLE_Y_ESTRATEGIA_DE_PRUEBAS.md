# Entorno reproducible y estrategia de pruebas

**Estado:** guía inicial H11, actualizada tras pruebas dirigidas; no certifica la suite global. Separar pruebas puras de pruebas con BD/ingesta/entrenamiento.

## Versiones y dependencias observadas

- CI usa Python **3.12**, Node **20**, `pip install -r backend/requirements.txt` y `npm ci` con `frontend/package-lock.json`. No hay lockfile Python completo comprobado; `requirements.txt` es la referencia actual.
- Host observado 2026-10-05: Python **3.14.4**, Node **24.21.0**, npm **11.19.0**. La venv heredada `backend/.venv` apunta a Python 3.12 ausente; se verificó en venv aislada temporal de Python 3.14. No se infiere reproducibilidad de un proceso local.
- Verificar primero con `python3 -m venv .venv` en un checkout/copia aislada (Python 3.12 recomendado para igualar CI), `.venv/bin/python -m pip install -r backend/requirements.txt`, `cd frontend && npm ci`. No copiar una venv entre hosts.

## Comandos seguros y gates

| Gate | Comando orientativo | Efectos / límite |
|---|---|---|
| Sintaxis Python | `python3 -m compileall -q backend` | Genera `__pycache__`; usar parseo AST si se requiere estrictamente cero escrituras. |
| Frontend lint | `cd frontend && npm run lint` | Solo lee código. |
| Frontend tests | `cd frontend && npm test` | Vitest; jsdom requiere dependencias instaladas. |
| Frontend build | `cd frontend && npm run build` | Escribe `dist/`; no despliega. |
| Backend unitarias puras | `cd backend && <venv>/python -m pytest -q <tests seleccionados>` | Examinar fixtures/side effects de cada grupo antes de correr; no usar suite global ciegamente. |
| Contratos API | `TestClient` con lifespan/BD simulados y stores temporales | No arrancar `app.py` contra BD operativa: su lifespan entrena al inicio. |
| Integración BD | PostgreSQL/SQLite **efímera**, `DATABASE_URL` de test explícita y fixtures sintéticas | Prohibido apuntar a producción, escribir ingestas o entrenar modelos productivos. |

## Estrategia para la reactivación

1. Tests estáticos de rutas montadas y ausencia de dependencias comerciales; tests de `X-Usuario-Id`/Bearer no autoritativos.
2. Unitarias de configuración global, bitácora, NBA y fútbol con fixtures sintéticas y sin red.
3. Contratos FE/BE de envelope, estado, escala y errores; datos no vacíos.
4. Integración en BD efímera con snapshot sintético de varias identidades y huérfanos; validar migración sin pérdida ni mezcla.
5. E2E local con backend/frontend ligados a loopback; verificar denegación desde fuera antes de quitar auth. No usar `scripts/dev.sh` con defaults anteriores que publican `0.0.0.0`; no detener los procesos que ya están corriendo sin necesidad.
6. CI en PR/branch: lint, typecheck/build, unitarias, contratos, integración efímera, analíticas y FE; gates proporcionales, sin entrenamientos o scrapers externos.

## Estado actual conocido

La CI se amplió a unitarias analíticas, contratos backend, tests frontend, lint y build. Aún no tiene PostgreSQL efímera ni test de integración de migración. `scripts/dev.sh` usa loopback por defecto y no libera puertos automáticamente; los procesos locales estaban detenidos en la comprobación posterior. No se certificó otro entorno.
