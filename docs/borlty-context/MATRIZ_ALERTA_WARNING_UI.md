# MATRIZ_ALERTA_WARNING_UI.md

Versión: 1.0  
Objetivo: diccionario canónico único de trazabilidad `alert_id -> warning.type -> UI variant`.

| alert_id | severidad alerta | warning.type contrato | warning.severity contrato | UI variant | acción UX |
|----------|------------------|-----------------------|---------------------------|-----------|-----------|
| DQ-CRIT-01 | CRITICA | quality | high | critical-banner | bloquear CTA apuesta / sugerir SKIP |
| DQ-CRIT-02 | CRITICA | quality | high | critical-banner | bloquear CTA apuesta / sugerir SKIP |
| DQ-CRIT-03 | CRITICA | drift | high | drift-critical-banner | marcar “En revisión” |
| DQ-CRIT-04 | CRITICA | stale | high | critical-banner | bloquear CTA apuesta / sugerir SKIP |
| DQ-HIGH-01 | ALTA | quality | medium | warning-panel | permitir con cautela |
| DQ-HIGH-02 | ALTA | incomplete | medium | warning-panel | permitir con cautela |
| DQ-HIGH-03 | ALTA | outlier | medium | warning-panel | permitir con cautela |
| DQ-HIGH-04 | ALTA | coverage | medium | warning-panel | permitir con cautela |
| DQ-HIGH-05 | ALTA | drift | high | drift-warning-panel | permitir con cautela reforzada |
| DQ-MED-01 | MEDIA | coverage | low | info-panel | informar |
| DQ-MED-02 | MEDIA | coverage | low | info-panel | informar |
| DQ-MED-03 | MEDIA | quality | low | info-panel | informar |
| DQ-MED-04 | MEDIA | quality | low | info-panel | informar |
| DQ-MED-05 | MEDIA | drift | medium | drift-info-panel | informar + seguimiento |

## Reglas de consistencia
1. Todo `alert_id` debe existir en esta matriz.
2. Si no existe mapeo, fallback a `warning.type=quality`, `warning.severity=medium`, `UI variant=warning-panel`.
3. Cambios de esta matriz requieren versionado y release notes del contrato.
