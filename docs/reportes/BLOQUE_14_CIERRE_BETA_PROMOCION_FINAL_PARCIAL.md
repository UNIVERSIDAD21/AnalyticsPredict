# BLOQUE 14 — Cierre de beta, promoción final parcial y limpieza de narrativa (fútbol)

## Decisión de cierre
**No se retira beta global de fútbol.**
Con la evidencia de bloques 10–13, el cierre correcto es: **operación por estados de mercado** + **promoción parcial solo cuando aplique**.

## Evidencia revisada (bloques 10–13)

Fuentes auditadas:
- `docs/reportes/BLOQUE_10_WALKFORWARD_SCORECARD_FUTBOL.json`
- `docs/reportes/BLOQUE_12_MONITOREO_AUTODEMOTION_FUTBOL.json`
- `docs/reportes/BLOQUE_13_SHADOW_MODE_OPERATIVO_FUTBOL.json`
- política canónica `backend/config/futbol_politica_promocion.json`

Hallazgo clave de cierre:
- En la corrida vigente no hay mercados en `PROMOCIONABLE`.
- La promoción global no es defendible.

## Tabla final de mercados por estado (corte actual)

Resumen:
- BLOQUEADO: 24
- LABORATORIO: 0
- VALIDACIÓN: 0
- PROMOCIONABLE: 0

Mercados (corte vigente) en BLOQUEADO:
- CORNERS_1T, CORNERS_2T, CORNERS_FT,
- CORNERS_LOCAL_1T, CORNERS_LOCAL_2T, CORNERS_LOCAL_FT,
- CORNERS_VISITANTE_1T, CORNERS_VISITANTE_2T, CORNERS_VISITANTE_FT,
- GOLES_1T, GOLES_2T, GOLES_FT,
- GOLES_LOCAL_1T, GOLES_LOCAL_2T, GOLES_LOCAL_FT,
- GOLES_VISITANTE_1T, GOLES_VISITANTE_2T, GOLES_VISITANTE_FT,
- DISPAROS_FT, DISPAROS_ARCO_FT,
- DISPAROS_LOCAL_FT, DISPAROS_LOCAL_ARCO_FT,
- DISPAROS_VISITANTE_FT, DISPAROS_VISITANTE_ARCO_FT.

## Narrativa de producto final (alineada)

- Fútbol no se comunica como módulo maduro global.
- Fútbol opera con **madurez diferenciada por mercado**.
- Todo mercado no promocionable se comunica en **PAPER/SHADOW** o validación restringida.
- La promoción es parcial, auditable y reversible por monitoreo + auto-demotion.

## Limpieza documental aplicada

- `docs/FUENTE_DE_VERDAD_ACTUAL.md`
  - deja explícita la regla de beta global con estados por mercado y promoción parcial reversible.
- `docs/arquitectura/ESTADO_PROYECTO.md`
  - refleja cierre por bloques 10–14 y estado real del módulo.
- `CHANGELOG.md`
  - registra el cierre de etapa y narrativa final.

## Criterio de revisión futura

Revisión obligatoria por ciclo (semanal/quincenal/mensual):
1. Re-ejecutar scorecard walk-forward.
2. Ejecutar monitoreo + auto-demotion.
3. Verificar estabilidad de ventanas consecutivas.
4. Solo promover mercados que cumplan umbral sostenido.

## Riesgos residuales

- Volumen resuelto insuficiente por mercado para salida de laboratorio/promoción.
- Persistencia de warnings técnicos frontend de bundling (no bloquea criterio cuantitativo, pero debe resolverse).

## Conclusión
Cierre honesto: **promoción parcial no habilitada aún**. Se mantiene beta global de fútbol con gobierno por mercado, no narrativa inflada.
