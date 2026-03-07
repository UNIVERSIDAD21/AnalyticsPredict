# CIERRE_BLOQUE_05_ESTABILIZACION.md

## Estado de cierre: bloque 05

Este bloque se considera **cerrado para progresión** (permite iniciar bloque 06),
pero **no cerrado totalmente**.

Diferencia explícita:
- **Cerrado para progresión:** hay control operativo, evidencia reproducible y policy temporal activa para riesgos críticos.
- **Cerrado totalmente:** requeriría erradicación completa de drift runtime, corrección definitiva de confidence y retiro de legado de contratos.

---

## Prioridad 1 — Confidence / Calibration bug

- **Estado real:** **PARCIAL**
- **Evidencia:**
  - `DIAGNOSTICO_CONFIDENCE_CALIBRATION.md`
  - `CONFIDENCE_POLICY_TEMPORAL.md`
  - `reports/auditoria_baselines/confidence_diagnostico_20260307T0108Z.json`
- **Decisión operativa vigente:**
  - no usar ALTA/MEDIA/BAJA como driver principal de stake,
  - usar confidence en modo explicativo/diagnóstico,
  - monitoreo por mercado de monotonicidad y calibración.
- **Estado de cierre en esta fase:** diagnóstico cerrado, corrección definitiva abierta.

---

## Prioridad 2 — Odds > 2.0

- **Estado real:** **CERRADO (temporal operativo)**
- **Policy vigente:**
  - no prohibición global de `>=2.0`,
  - bloqueo específico `COMPLETO >=2.0`,
  - restricciones en buckets frágiles (ej. `COMPLETO 1.6–1.8`, Q3/Q4 conservador),
  - buckets con `n < 20`: “cautela / muestra insuficiente”.
- **Guardrails:**
  - revisión periódica por bucket,
  - ajuste de severidad si ROI negativo persiste en ventanas consecutivas.
- **Evidencia:**
  - `REGLA_FORMAL_ODDS_ALTAS.md`
  - `MATRIZ_DE_POLICY_POR_ODDS_Y_MERCADO.md`
  - `reports/auditoria_baselines/odds_policy_evidence_20260307T0112Z.json`

---

## Prioridad 3 — Contratos backend/frontend

- **Estado real:** **PARCIAL**
- **Convención mínima lograda:**
  - contrato canónico mínimo definido,
  - parser central de errores robustecido (`detail/message/mensaje/error.*`).
- **Deuda legacy restante:**
  - convivencia de envelope y objeto directo,
  - endpoints legacy aún heterogéneos en éxito/error/naming,
  - transición incremental pendiente (sin migración masiva).
- **Evidencia:**
  - `CONTRATO_API_CANONICO_MINIMO.md`
  - `MATRIZ_ENDPOINT_FRONTEND_BACKEND.md`
  - `PLAN_TRANSICION_CONTRATOS.md`

---

## Prioridad 4 — Drift de esquema

- **Estado real:** **PARCIAL (alto residual)**
- **Qué ya quedó instrumentado:**
  - esquema canónico definido para `apuestas_futbol`,
  - mapa código ↔ columnas ↔ tablas,
  - warnings anti-drift en runtime cuando se usa fallback legacy.
- **Qué falta para cierre total:**
  1. observabilidad 7–14 días sobre uso real de columnas legacy,
  2. recolección de evidencia por entorno,
  3. primer recorte seguro de fallbacks innecesarios,
  4. deprecación progresiva sin ruptura.
- **Evidencia:**
  - `ESQUEMA_CANONICO_APUESTAS_FUTBOL.md`
  - `MAPA_DE_COLUMNAS_LEGACY_VS_CANONICAS.md`
  - `PLAN_ANTI_DRIFT_Y_DEPRECACION.md`

---

## Deuda residual activa del bloque 05

1. Corrección definitiva de confidence/calibration por mercado (no solo policy temporal).
2. Contratos legacy coexistentes en parte de la API.
3. Drift runtime aún activo en zonas fútbol con fallback.
4. Necesidad de consolidar observabilidad anti-drift y ejecutar recorte controlado.

---

## Riesgos abiertos

1. Sobreconfianza operativa si se asume confidence ya resuelto.
2. Reaparición de inconsistencias por contratos legacy en endpoints menos usados.
3. Inestabilidad métrica si drift de columnas cambia comportamiento por entorno.
4. Sobreajuste de policy de odds en buckets con muestra baja.

---

## Seguimiento operativo mientras avanza bloque 06

1. Monitoreo semanal de confidence por mercado (hit/ROI/calibración).
2. Monitoreo de cumplimiento de policy de odds por bucket.
3. Revisión de logs anti-drift y conteo de uso legacy.
4. Mantener parser central de errores como capa de compatibilidad activa.
5. No declarar cierre total de bloque 05 hasta completar recorte de fallback y validación estable por mercado.

---

## Conclusión formal

Bloque 05 queda **cerrado para progresión a bloque 06**, con deuda residual explícita y controles temporales activos.
No queda presentado como erradicación total.
