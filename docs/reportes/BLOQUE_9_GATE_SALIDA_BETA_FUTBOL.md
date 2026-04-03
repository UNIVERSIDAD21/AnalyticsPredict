# BLOQUE 9 — Gate cuantitativo de salida beta (módulo fútbol)

## Decisión operativa del bloque
**Estado global actual: BETA_LAB (no promocionable como módulo maduro).**

Se implementó gate cuantitativo reproducible por mercado y endurecimiento de UX para no insinuar madurez donde no existe.

---

## 1) Inventario real de madurez por mercado (evidencia)

Fuente automática ejecutada:
- `backend/scripts/reporte_madurez_futbol_beta.py --dias 180 --out docs/reportes/BLOQUE_9_MADUREZ_FUTBOL_AUTO.json`

Resultado observado en esta corrida:
- Mercados evaluados: 24
- Clasificación:
  - **NO_APTO:** 24
  - **EXPERIMENTAL:** 0
  - **VALIDACION:** 0
  - **PROMOCIONABLE:** 0

Razón dominante detectada:
- volumen/resolución crítica y falta de estabilidad operativa suficiente para promoción.

> Nota: este bloque no “maquilla” el estado: en el snapshot actual, fútbol permanece en laboratorio.

---

## 2) Criterios cuantitativos formales (promoción/bloqueo)

Definidos en `backend/motor_futbol/madurez_beta.py`:

### Umbrales de VALIDACIÓN
- `min_resueltas_validacion = 120`
- `min_lineas_validacion = 2`
- `min_resolved_rate_validacion = 0.70`
- `max_fallback_rate_validacion = 0.35`

### Umbrales de PROMOCIÓN
- `min_resueltas_promocion = 250`
- `min_lineas_promocion = 4`
- `max_brier_promocion = 0.23`
- `max_logloss_promocion = 0.67`
- `max_ece_promocion = 0.06`
- `min_resolved_rate_promocion = 0.85`
- `max_fallback_rate_promocion = 0.15`
- `max_window_drift_promocion = 0.03`

### Clasificación por mercado
- `NO_APTO`
- `EXPERIMENTAL`
- `VALIDACION`
- `PROMOCIONABLE`

Sin cumplir umbral, no hay promoción.

---

## 3) Reporte automático de madurez

### Endpoint nuevo
- `GET /api/futbol/metricas/madurez-beta`
- Devuelve:
  - estado global del módulo,
  - matriz por mercado,
  - bloqueados,
  - candidatos promoción,
  - riesgos activos,
  - criterios usados.

### Script reproducible nuevo
- `backend/scripts/reporte_madurez_futbol_beta.py`
- Genera JSON en `docs/reportes/BLOQUE_9_MADUREZ_FUTBOL_AUTO.json`

---

## 4) Modo shadow / paper trading estricto

Criterio implementado en gate:
- Mercados **!= PROMOCIONABLE** deben operar como validación/sombra:
  - se analizan,
  - se registran métricas,
  - se monitorea performance,
  - **no se comunican como maduros**.

Este criterio queda explícito en el payload de madurez (`modo_operativo_recomendado`).

---

## 5) Endurecimiento de gate frontend

En `ResultadoAnalisis`:
- Si hay señales críticas (`estado_mercados_vacio`, `mercado_objetivo_fuera_estado_mercados`, muestra insuficiente severa, datos incompletos):
  - se muestra banner de **MODO VALIDACIÓN BETA**,
  - se evita presentar bloques contextuales/razones como si fueran soporte profesional pleno,
  - se mantiene salida honesta y no promocional.

Además, el adaptador propaga advertencias de severidad de coverage.

---

## 6) Pruebas y evidencia

Backend:
- `backend/tests/test_futbol_madurez_beta.py` (nuevo)
- `backend/tests/test_futbol_gating_contexto_unittest.py`
- Resultado: **9 passed**

Frontend:
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts`
- `frontend/src/servicios/futbol/analisis.test.ts`
- Resultado: **6 passed**

Calidad build:
- `npm run lint` ✅
- `npm run build` ✅

---

## 7) Archivos tocados

- `backend/motor_futbol/madurez_beta.py` (nuevo)
- `backend/tests/test_futbol_madurez_beta.py` (nuevo)
- `backend/api/schemas_futbol.py`
- `backend/api/rutas_metricas_futbol.py`
- `backend/scripts/reporte_madurez_futbol_beta.py` (nuevo)
- `docs/reportes/BLOQUE_9_MADUREZ_FUTBOL_AUTO.json` (nuevo, generado)
- `frontend/src/componentes/organismos/ResultadoAnalisis.tsx`
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.ts`
- `frontend/src/utilidades/adaptadores/futbolToNbaAnalisis.test.ts`
- `CHANGELOG.md`
- `docs/arquitectura/ESTADO_PROYECTO.md`

---

## 8) Riesgos residuales

- Estado de mercados histórico aún limitado por volumen resolutivo: bloquea promoción real.
- Múltiples mercados siguen con fallback alto.
- El warning de chunk circular frontend persiste como deuda técnica (no bloquea CI actual).

---

## 9) Criterio formal de promoción beta → confiable

Un mercado solo puede subir a `PROMOCIONABLE` si cumple simultáneamente:
1. volumen resuelto mínimo,
2. cobertura de líneas suficiente,
3. `estado_mercados` estable,
4. calibración (Brier/LogLoss/ECE) dentro de umbral,
5. baja degradación/fallback,
6. estabilidad temporal por ventana.

Si falla uno de estos, no se promociona.
