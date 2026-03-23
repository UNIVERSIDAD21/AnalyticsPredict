# COBERTURA_TESTS_B08

## Tabla resumen de cobertura

| Módulo | Tests unitarios | Tests integración | Hard-checks |
|---|---:|---:|---|
| `backend/calidad/scorecard.py` | 4 | 2 | Crítica activa no puede nivel A |
| `backend/calidad/alertas.py` | 4 | 2 | Drift rojo 3+ días y no silenciamiento |
| `backend/explicabilidad/contrato.py` | 5 | 4 | A + warning crítico => `QualityCoherenceError` |
| Endpoints (`/api/calidad/alertas`, `/api/prediccion/{id}/explicacion`) | smoke parcial | 2 | envelope y códigos esperados |

## DEUDA NO CUBIERTA POR TESTS

1. Drift runtime real en producción con datos multi-entorno (solo cubierto con mocks/sintético).
2. Confidence/calibration real por mercado en ventanas largas (requiere datasets reales históricos).
3. Comportamiento legacy completo de todos los consumidores externos (requiere pruebas integradas con clientes reales).
4. Rendimiento de scorecard/alertas bajo carga de producción (requiere test de performance dedicado).
5. Validación UI end-to-end con datos en vivo (se cubre en bloque frontend QA, no en esta suite backend).

> Nota de gobernanza: la deuda del bloque 05 sigue activa y visible; estos tests validan coherencia técnica, no “resolución” de deuda.
