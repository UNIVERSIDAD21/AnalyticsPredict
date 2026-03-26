# Ruta de Auditoría C0–C7 (AnalyticsPredict)

Fecha: 2026-03-24
Estado general: Pre-lanzamiento comercial, con C1 aún EN_CURSO por validación manual final de MP.

## 1) Punto de entrada (fuente de verdad)
1. `docs/arquitectura/ESTADO_PROYECTO.md`
2. `CHANGELOG.md`
3. `docs/arquitectura/ADR-005-alcance-comercial-minimo-c0.md`
4. `docs/arquitectura/PLAN_BLOQUES_C0_C7_LANZAMIENTO_PROFESIONAL.md`
5. `docs/comercial/publico/00_INDICE_PLAN_PUBLICO_NEGOCIO.md` (prioridades P1–P9 por olas)

## 2) Work orders oficiales
- `docs/work_orders/c0_c7/00_INDICE_WORK_ORDERS_C0_C7.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C0_REALINEACION_GO_LIVE.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C1_PAGOS_PRODUCTIVOS.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C2_HARDENING_Y_PERSISTENCIA.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C3_CUMPLIMIENTO_COMERCIAL.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C4_ACTIVACION_Y_ENTRADA_DE_VALOR.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C5_PARIDAD_OPERATIVA_FUTBOL.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C6_CENTRO_ANALITICO_MULTIDEPORTE.md`
- `docs/work_orders/c0_c7/WORK_ORDER_C7_GATE_COMERCIAL_Y_COHORTE.md`

## 3) Evidencia por bloque ejecutado
### C0 (cerrado)
- Decisión y realineación de alcance comercial: ADR-005 + ESTADO/CHANGELOG.

### C1 (en curso)
- Evidencia técnica equivalente E2E: `docs/reportes/C1_E2E_PRIMER_PAGO_VALIDACION_EQUIVALENTE_2026-03-24.md`
- Template de cierre manual real: `docs/reportes/C1_CIERRE_MANUAL_MERCADOPAGO_TEMPLATE.md`
- Flujo y matriz operativa: `docs/operacion/FLUJO_REAL_PAGOS_C1.md`, `docs/operacion/C1_MATRIZ_ESTADOS_Y_FALLOS.md`

### C2 (cerrado)
- `docs/reportes/C2_BACKUP_RESTORE_TEST_2026-03-24.md`
- artefactos operativos C2 en docs/operacion y scripts asociados.

### C3 (cerrado)
- `docs/comercial/C3_CUMPLIMIENTO_COMERCIAL_MINIMO.md`
- `docs/comercial/C3_MATRIZ_COBERTURA_LEGAL_COMERCIAL_FLUJOS_PREMIUM.md`
- `docs/comercial/C3_CHECKLIST_VALIDACION_LEGAL_OPERATIVA.md`
- `docs/reportes/C3_REVISION_CONSISTENCIA_UI_BACKEND_LEGAL_2026-03-24.md`

### C4 (cerrado)
- `docs/comercial/C4_INVENTARIO_FLUJO_ACTUAL_Y_FRICCIONES.md`
- `docs/comercial/C4_FLUJO_ACTIVACION_REFINADO.md`
- `docs/comercial/C4_MATRIZ_CAPACIDADES_POR_TIPO_USUARIO.md`
- `docs/comercial/C4_KPIS_ACTIVACION_VALOR_REAL.md`
- `docs/reportes/C4_REVISION_COPY_Y_PROPUESTA_VALOR_2026-03-24.md`

### C5 (cerrado)
- `docs/comercial/C5_CONTRATO_CANONICO_FUTBOL.md`
- `docs/comercial/C5_CHECKLIST_MADUREZ_FUTBOL.md`
- `docs/comercial/C5_CRITERIOS_PROMOCION_COMERCIAL_FUTBOL.md`
- `docs/reportes/C5_REVISION_PARIDAD_OPERATIVA_FUTBOL_2026-03-24.md`

### C6 (cerrado)
- `docs/comercial/C6_INVENTARIO_VISTAS_NBA_FUTBOL.md`
- `docs/comercial/C6_CONTRATO_BASE_METRICAS_COMUNES.md`
- `docs/comercial/C6_MADUREZ_VISIBLE_POR_DEPORTE.md`
- `docs/reportes/C6_EJECUCION_CENTRO_ANALITICO_MULTIDEPORTE_2026-03-24.md`

## 4) Código a revisar (muestras clave)
- C1 pagos: `backend/api/rutas_pagos.py` (o ruta equivalente integrada), `backend/servicios/*pago*`
- C5 fútbol sin mock temporal: `backend/api/rutas_metricas_futbol.py`, `frontend/src/componentes/paginas/DashboardFutbol.tsx`
- C6 multideporte: `frontend/src/componentes/paginas/PaginaCentroAnalitico.tsx`, `frontend/src/componentes/organismos/Encabezado.tsx`, `frontend/src/App.tsx`

## 5) Estado de readiness para C7
- C7 sigue bloqueado por C1.
- C1 requiere validación manual real de MP en entorno con dominio/URL pública final y callback estable.
- Sin ese cierre manual no procede gate comercial final.
- Nota para auditoría: mejoras de UI/UX, Ola 1/2/3 o validaciones equivalentes no reemplazan este requisito de cierre comercial real.

## 6) Trazabilidad Git
- Revisar historial en `main` con commits de C0..C6.
- Commits recientes clave:
  - `a252dc9` C3
  - `9902fbd` C4
  - `06bae0a` C5
  - `20f028f` C6

## 7) Veredicto auditivo actual
- Proyecto documentado y trazable para C0, C2, C3, C4, C5, C6.
- C1 técnicamente preparado pero no cerrado por dependencia externa (dominio/validación MP real).
- C7 no debe ejecutarse aún.
