# CONTROLES_COHERENCIA_CALIDAD_EXPLICABILIDAD.md

Versión: 1.0  
Objetivo: cerrar gaps críticos de coherencia entre calidad (07.1) y explicabilidad (07.2).

## 1) Hard-check obligatorio: nivel A sin warnings críticos

### Regla de negocio
No se permite publicar una explicación con:
- `data_quality.level = "A"`
- y al menos un warning crítico (`severity = "critical"`) en `data_quality.flags` o `explanation.warnings`.

### Resultado esperado
- Si ocurre inconsistencia, forzar degradación automática a `level = "B"`.
- Registrar evento de coherencia en logs y métrica de calidad contractual.

### Pseudocódigo backend
```python
def enforce_quality_gate(payload):
    has_critical = any(f.get("severity") == "critical" for f in payload["data_quality"].get("flags", [])) or \
                   any(w.get("severity") == "high" and w.get("type") == "quality" for w in payload["explanation"].get("warnings", []))

    if payload["data_quality"]["level"] == "A" and has_critical:
        payload["data_quality"]["level"] = "B"
        payload.setdefault("metadata", {})["coherence_adjusted"] = True
        payload["metadata"]["coherence_reason"] = "A_with_critical_warning_not_allowed"
    return payload
```

## 2) Validación CI (contract test)

### Caso obligatorio en pipeline
- Input: payload con `level=A` y warning crítico.
- Expected: test falla si no hay degradación a B o rechazo de respuesta.

### Regla de aceptación CI
- Build bloquea merge si cualquier test de coherencia contractual falla.

## 3) SQL de control operativo

```sql
-- Detecta inconsistencias publicadas (debería retornar 0)
SELECT COUNT(*) AS incoherencias
FROM analytics.prediction_explanations e
WHERE e.data_quality_level = 'A'
  AND (
    EXISTS (
      SELECT 1
      FROM jsonb_array_elements(COALESCE(e.data_quality_flags, '[]'::jsonb)) f
      WHERE f->>'severity' = 'critical'
    )
    OR EXISTS (
      SELECT 1
      FROM jsonb_array_elements(COALESCE(e.explanation_warnings, '[]'::jsonb)) w
      WHERE (w->>'severity' = 'high' AND w->>'type' = 'quality')
    )
  );
```

## 4) Criterio de cumplimiento

Se considera cerrado el gap cuando:
1. regla hard-check está definida en contrato y backend,
2. test CI obligatorio está incorporado,
3. query de control retorna 0 en validaciones de staging.
