# RUNBOOK_DRIFT_FUTBOL

Fecha: 2026-03-09  
Versión: 1.0

## Objetivo
Reducir falsos positivos de drift fútbol sin silenciar eventos críticos reales.

## Cooldowns por tipo de alerta

| Alerta | Nivel | Cooldown | Regla |
|---|---|---:|---|
| DQ-MED-05 | MEDIA (yellow) | 3 periodos | Evita spam por oscilación yellow/none |
| DQ-HIGH-05 | ALTA (orange) | 1 periodo | Mantiene urgencia sin duplicación ruidosa |
| DQ-CRIT-03 | CRITICA (red 3+) | 0 periodos (sin cooldown) | Invariante crítico: siempre activa si persiste |

## Criterio manual de override

Se permite override manual solo para MED/HIGH en incidentes confirmados como falsos positivos.

No se permite override para DQ-CRIT-03 mientras `drift_consecutivo_rojo >= 3`.

## Procedimiento operativo cuando drift rojo persiste 7+ días

1. Confirmar que DQ-CRIT-03 sigue emitiéndose (sin cooldown).
2. Abrir incidente de severidad CRÍTICA (data reliability).
3. Ejecutar diagnóstico de raíz:
   - contratos canónicos vs legacy,
   - integridad ingestión fútbol,
   - cobertura/freshness por fuente.
4. Mantener visible deuda B05 en `/api/calidad/estado-sistema`.
5. Definir plan de mitigación con checkpoint diario hasta salir de rojo.

## Gobernanza

- Este runbook no resuelve drift B05; solo controla ruido operativo.
- `drift_futbol_parcial_alto` debe seguir reportándose como deuda activa.
