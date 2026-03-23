# GOBIERNO_DE_MODELOS

Versión: 1.0  
Fecha: 2026-03-09

## 1. Registro formal de modelos

### 1.1 Tabla de registro
Fuente: `modelo_versiones` (BD real, `backend/estructuraBD.txt`).

Campos mínimos operativos:
- `version`
- `fecha_entrenamiento`
- `mae_q1`, `mae_q2`, `mae_q3`, `mae_q4`
- `hash_datos`
- `cutoff_entrenamiento`
- `metadata` (config/artefactos)

### 1.2 Aprobación
- Owner técnico: Lead DS + Arquitecto backend.
- Owner producto: Product Owner.
- Regla: ningún modelo pasa a “candidato” sin comparación contra baseline vigente y evidencia SQL.

## 2. Comparación y métricas oficiales

### 2.1 NBA (predicción por cuarto)
- Métrica principal: MAE por cuarto (`mae_q1..mae_q4`).
- Agregado para decisión: promedio MAE de Q1..Q4.

### 2.2 Calibración de confianza
- Métricas obligatorias: `Brier`, `ECE`, `LogLoss`.
- Fuente: `analytics.vw_calibration_scorecard` + tabla `calibradores`.

## 3. Criterios de promoción (numéricos)

Un modelo/calibrador es candidato si cumple:
1. NBA: mejora MAE promedio >3% vs baseline activo.
2. Calibración: mejora Brier >2% y ECE <0.05.
3. LogLoss no empeora >3%.
4. Validación en staging sin regresión funcional.

## 4. Rollback operativo

Trigger de rollback:
- degradación sostenida (>3 días) en métricas críticas,
- alertas críticas de coherencia o drift rojo persistente,
- regresión funcional en endpoints productivos.

Procedimiento:
1. Congelar promoción nueva.
2. Revertir versión activa en capa de serving/flag.
3. Notificar incidente y abrir postmortem.
4. Registrar en bitácora de modelos.

## 5. Trazabilidad de experimentos

Estructura mínima de trazabilidad:
- `version` + `hash_datos` + `cutoff_entrenamiento`
- `config_entrenamiento` en `metadata`
- métricas antes/después (MAE por cuarto, Brier/ECE/LogLoss)

## 6. Invariante de deuda B05

- `confidence_parcial` sigue **EN_PROCESO**.
- No declarar RESUELTO sin 30+ días en producción con criterios cumplidos.
- Baselines fútbol se etiquetan con deuda activa si `drift_futbol_parcial_alto` sigue ACTIVO.
