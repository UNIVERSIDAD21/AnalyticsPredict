# BLOQUE 14 — Cierre de beta, promoción final parcial y limpieza de narrativa (fútbol)

## Cierre ejecutivo

Cierre **honesto y defendible**: con evidencia de bloques 10–13, fútbol **NO** sale de beta global en esta corrida.

Se reemplaza la narrativa binaria por una narrativa profesional:
- fútbol opera con **madurez diferenciada por mercado**,
- la promoción es **parcial, auditable y reversible**,
- el estado de cada mercado depende de scorecards + monitoreo continuo + shadow mode.

## Evidencia revisada (bloques 10–13)

Fuentes usadas:
- `docs/reportes/BLOQUE_10_WALKFORWARD_SCORECARD_FUTBOL.json`
- `docs/reportes/BLOQUE_12_MONITOREO_AUTODEMOTION_FUTBOL.json`
- `docs/reportes/BLOQUE_13_SHADOW_MODE_OPERATIVO_FUTBOL.json`
- `backend/config/futbol_politica_promocion.json`

Hallazgos clave:
- Walk-forward/scorecard (B10):
  - `BLOQUEADO`: 24
  - `LABORATORIO`: 0
  - `VALIDACION`: 0
  - `PROMOCIONABLE`: 0
- Monitoreo/autodemotion (B12): degradaciones ejecutables por regla conservadora; no auto-promoción.
- Shadow mode (B13): operación longitudinal activa y trazable, con visibilidad de estado operativo por mercado.

## Tabla final de mercados por estado (snapshot cierre)

### BLOQUEADO (24)
- CORNERS_1T
- CORNERS_2T
- CORNERS_FT
- CORNERS_LOCAL_1T
- CORNERS_LOCAL_2T
- CORNERS_LOCAL_FT
- CORNERS_VISITANTE_1T
- CORNERS_VISITANTE_2T
- CORNERS_VISITANTE_FT
- GOLES_1T
- GOLES_2T
- GOLES_FT
- GOLES_LOCAL_1T
- GOLES_LOCAL_2T
- GOLES_LOCAL_FT
- GOLES_VISITANTE_1T
- GOLES_VISITANTE_2T
- GOLES_VISITANTE_FT
- DISPAROS_FT
- DISPAROS_ARCO_FT
- DISPAROS_LOCAL_FT
- DISPAROS_LOCAL_ARCO_FT
- DISPAROS_VISITANTE_FT
- DISPAROS_VISITANTE_ARCO_FT

### LABORATORIO
- (ninguno en este snapshot)

### VALIDACIÓN
- (ninguno en este snapshot)

### PROMOCIONABLE
- (ninguno en este snapshot)

## Narrativa de producto final (post-bloque 14)

- **No** se declara “fútbol terminado”.
- **Sí** se declara que fútbol está gobernado por estados por mercado.
- **Sí** se mantiene beta global mientras no exista evidencia de promoción parcial sostenida.
- **Sí** se evita comunicación ambigua en UI para mercados no promocionables.

## Riesgos residuales

- Volumen resuelto insuficiente sigue bloqueando promoción real.
- Sin incremento de coverage/estabilidad temporal, no hay base para transición a validación/promoción.
- Persisten advertencias técnicas de bundling frontend (no bloquean el gate de madurez).

## Criterio explícito de revisión futura

Revisión de cierre beta parcial en cada corte mensual o cuando:
1. al menos 1 mercado alcance `VALIDACION` sostenida,
2. al menos 1 mercado alcance `PROMOCIONABLE` en ventanas consecutivas,
3. monitoreo continuo no dispare demotion en el periodo de observación.

Hasta entonces, se mantiene:
- beta global,
- operación shadow/paper por mercado,
- promoción parcial deshabilitada por falta de evidencia.
