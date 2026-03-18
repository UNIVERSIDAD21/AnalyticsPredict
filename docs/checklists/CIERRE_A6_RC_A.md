# Checklist de cierre A6 — Gate RC-A

Objetivo: validar de forma integral que A2+A3+A4+A5 no tienen bloqueantes P0/P1 antes de pasar a monetización (B1/B2/B3).

## Ejecución rápida

Desde la raíz del repo:

```bash
scripts/validar_a6_rca.sh
```

## Qué valida el script

1. Backend (pytest)
   - `backend/tests/api/test_auth_endpoints.py`
   - `backend/tests/api/test_bitacora_contract.py`
   - `backend/tests/api/test_apuestas_futbol_contract.py`
   - `backend/tests/test_observabilidad_http.py`
   - `backend/tests/test_observabilidad_http_endpoint.py`
   - `backend/tests/test_smoke_api.py`
2. Frontend
   - `npm run lint`
   - `npm run build`
3. Evidencia
   - Genera reporte timestamp en `docs/reportes/A6_RC-A_<UTC>.md`

## Criterio de cierre

A6 se considera **CERRADO** cuando:
- Script finaliza en verde.
- Reporte RC-A queda generado en `docs/reportes/`.
- Estado de bloque actualizado en `docs/arquitectura/ESTADO_PROYECTO.md`.
- Entrada registrada en `CHANGELOG.md`.
