# AUDITORIA_TECNICA_Y_ANALITICA.md

## Resumen ejecutivo

Se completó una auditoría técnica estática del repositorio (backend + frontend + esquema SQL/migraciones + contratos API).

**Resultado general:**
- La base del sistema está viva y amplia (FastAPI + React + dominios NBA/Fútbol + capa de métricas).
- NBA se ve más consolidado en términos de flujo operativo histórico.
- Fútbol tiene mucha superficie funcional, pero aún presenta señales de producto parcialmente consolidado (UI con datos mock/TODO, y un endpoint consumido por frontend que no existe en backend).
- Hay deuda importante en consistencia de contratos, naming y compatibilidad de esquema.

> Importante: la validación cuantitativa de baselines (81.48% win rate, 11.53% ROI, paradoja confidence, odds>2.0, quarter>full-game) **no pudo cerrarse de forma concluyente** en esta fase porque no hay conexión DB activa en este entorno (sin `.env` operativo ni ejecución de consultas productivas).

---

## Alcance y evidencia usada

### Fuentes auditadas
- `docs/borlty-context/00..10_*.md`
- Backend FastAPI (`backend/app.py`, `backend/api/rutas*.py`, `backend/motor*`, `backend/motor_futbol*`)
- Frontend React (`frontend/src/componentes`, `frontend/src/servicios`, `frontend/src/hooks`, `frontend/src/tipos`)
- SQL/migraciones (`backend/scripts/sql/*`)
- Documentación operativa (`README.md`)

### Limitaciones de esta fase
- No hay `pytest` instalado en este entorno (`pytest: command not found`).
- No hay credenciales DB operativas cargadas en runtime local para verificar baselines numéricos con queries reales.

---

## Arquitectura backend real (FastAPI)

### Estructura observada
- App principal en `backend/app.py`
- ~15 routers (`backend/api/rutas*.py`)
- Dominios:
  - NBA: análisis, bitácora, métricas, predicciones, backtest
  - Fútbol: análisis, partidos, equipos, competiciones, apuestas, métricas
  - Interno: recalibración, resolución, alertas, jobs

### Fortalezas
- Cobertura amplia de endpoints (79 rutas detectadas).
- Manejo de política de calidad y modo estricto (NBA y fútbol).
- Persistencia de predicciones y capas de calibración.
- Separación razonable por módulos (`api/`, `motor/`, `motor_futbol/`, `servicios/`).

### Hallazgos técnicos
1. **Acoplamiento fuerte API ↔ SQL crudo**
   - Alta dependencia de SQL inline en rutas.
2. **Compatibilidad defensiva por drift**
   - En `rutas_apuestas_futbol.py` hay resolución dinámica de columnas (`estado|status`, `cuota|odds|cuota_decimal`, etc.).
   - Señal de esquema no completamente canónico.
3. **Convenciones de respuesta mixtas**
   - Algunos endpoints retornan envelope `{ exito, ... }`, otros retorno directo de modelo.
4. **Convenciones de errores no homogéneas**
   - Hay errores de FastAPI (`detail`) y errores envelope personalizados.

---

## Arquitectura frontend real (React + TS)

### Superficie funcional observada
- ~10 páginas en `frontend/src/componentes/paginas`
- ~17 servicios API
- ~13 hooks
- Flujos implementados para NBA y Fútbol

### Fortalezas
- Cliente HTTP centralizado (`frontend/src/servicios/api.ts`).
- Transformadores para normalizar snake_case → camelCase en algunos módulos.
- Cobertura visual amplia para métricas, bitácora, análisis y dashboards.

### Hallazgos técnicos
1. **Consumo de endpoint inexistente**
   - Front usa `/api/futbol/apuestas/estadisticas`.
   - Ese endpoint no aparece en backend.
2. **UI parcialmente mock en fútbol**
   - `DashboardFutbol.tsx` genera serie temporal con `generarDatosTemporales()` (mock explícito).
3. **Funcionalidad pendiente visible en UI**
   - `BitacoraFutbol.tsx` incluye `TODO: Implementar edicion`.
4. **Parsing de errores puede perder mensaje real**
   - `extraerMensajeError()` prioriza `error.mensaje` mientras backend suele usar `detail` o `message`.

---

## Estado real de BD (inferido por código + migraciones)

### Tablas/objetos relevantes detectados
- NBA: `partidos_baloncesto`, `equipos`, `predicciones_registradas`, `apuestas`, `calibradores`, `modelo_versiones`, etc.
- Fútbol: `partidos_futbol`, `equipos_futbol`, `competiciones_futbol`, `predicciones_futbol`, `apuestas_futbol`, `calibradores_futbol`, `modelo_versiones_futbol`, etc.
- Calidad/operación: `alertas_calibracion`, `ingestion_state_futbol`, `ingestion_state_baloncesto`, vistas de métricas.

### Hallazgo crítico de esquema
- Uso de fallback dinámico de columnas en rutas de apuestas fútbol sugiere:
  - coexistencia de esquemas históricos,
  - naming inconsistente,
  - necesidad de esquema canónico y plan de migración/deprecación.

---

## Flujos principales del sistema

1. **Análisis NBA**
   - `POST /api/analizar`, `POST /api/analizar-en-vivo`
   - Registra predicciones y aplica gates de calidad.

2. **Análisis Fútbol**
   - `POST /api/futbol/analizar`
   - Genera predicciones multi-mercado y recomendaciones condicionadas por calidad.

3. **Bitácora/Apuestas**
   - NBA: `/api/bitacora*`
   - Fútbol: `/api/futbol/apuestas*`

4. **Métricas y control operativo**
   - `/api/metricas/*`
   - `/api/futbol/metricas/*`
   - `/api/interno/*`

---

## Validación o refutación de baselines (fase 0)

| Baseline | Estado fase 0 | Evidencia actual |
|---|---|---|
| NBA win rate 81.48% | ⚠️ No concluyente | Requiere query/reporte productivo actual |
| NBA ROI 11.53% | ⚠️ No concluyente | Requiere query/reporte productivo actual |
| HIGH confidence peor que MEDIUM/LOW | ⚠️ No concluyente | Lógica de confidence existe, pero falta contraste con outcomes reales |
| Odds > 2.0 ROI negativo | ⚠️ No concluyente | Falta segmentación real por odds desde BD |
| Quarter markets > full-game | ⚠️ No concluyente | Falta benchmark cuantitativo actualizado |
| Estado operativo NBA | ✅ Parcialmente validado | Cobertura endpoints, registro y métricas presentes |
| Estado operativo Football | ✅ Parcialmente validado | Cobertura amplia, pero UI/contratos aún con brechas |

---

## Fortalezas reales detectadas

1. Backend con amplitud funcional y módulos de control de calidad.
2. Cobertura dual NBA/Fútbol ya integrada.
3. Métricas y monitoreo no triviales disponibles por API.
4. Mecanismos de calibración y policy gates presentes.
5. Documentación operativa y comandos de ciclo (`make`) existentes.

## Problemas reales detectados

1. Inconsistencia de contratos backend/frontend (al menos 1 endpoint huérfano en frontend).
2. Convenciones heterogéneas de respuesta/error.
3. Señales de drift de esquema (fallbacks de columnas en runtime).
4. Parte del frontend fútbol aún no 100% productivo (mock + TODO).
5. Baselines críticos de negocio no validados en esta fase por falta de acceso DB operativo.

---

## Riesgos técnicos y analíticos principales

1. **Riesgo de decisiones con métricas no verificadas** (baseline antiguo vs realidad actual).
2. **Riesgo de integridad contractual** (frontend invocando rutas inexistentes).
3. **Riesgo de mantenimiento** por compatibilidad forzada de esquema.
4. **Riesgo de credibilidad** si dashboards mezclan datos reales con mock sin señal clara.
5. **Riesgo de calibración/stake** si paradoja de confidence sigue activa sin cierre analítico.

---

## Conclusión de fase 0

El sistema **sí tiene base de plataforma**, pero todavía no está en estado de “fuente única de verdad analítica” por:
- brechas de contratos,
- drift de esquema,
- y baselines críticos sin revalidación cuantitativa reciente.

Siguiente paso recomendado (sin refactor masivo): cerrar validación de baselines sobre BD real + unificación de contratos + saneamiento semántico de respuestas/error.
