# REGLA_FORMAL_ODDS_ALTAS.md

## Objetivo
Cerrar una regla operativa temporal, formal y defendible sobre odds altas, usando evidencia acumulada del bloque 05 sin refactor masivo.

## Alcance de evidencia reutilizada
- `VALIDACION_CUANTITATIVA_BASELINES_NBA.md`
- `ANALISIS_SEGMENTOS_NBA.md`
- `ANALISIS_HISTORICO_COMPLETO_NBA.md`
- Evidencia complementaria:
  - `reports/auditoria_baselines/odds_policy_evidence_20260307T0112Z.json`
  - SQL: `docs/borlty-context/sql/ODDS_POLICY_VALIDACION.sql`

---

## Problema exacto
La regla histórica “odds >= 2.0 son malas” no se sostiene de forma uniforme entre datasets y mercados:
- en dataset corto aparece muy negativa,
- en histórico ampliado global puede verse positiva,
- pero en **full-game >=2.0** persiste señal negativa.

Por tanto, una regla global única sería técnicamente débil.

---

## Evidencia clave (resumen)

1. **Dataset corto (`apuestas`)**
- `>=2.0`: ROI muy negativo (muestra pequeña).

2. **Dataset ampliado (deduplicado de `predicciones_registradas`)**
- Global `>=2.0`: ROI positivo en promedio.
- **COMPLETO `>=2.0`: ROI negativo**.
- Q1/Q2 muestran buckets >2.0 potencialmente positivos, pero con variabilidad de muestra.
- Q3/Q4 mantienen perfil más riesgoso en varios buckets.

3. **Edge declarado vs resultado**
- En varios buckets, `edge_medio` sale positivo mientras ROI real no acompaña (especialmente full-game >=2.0).
- Esto sugiere que pricing/estimación de probabilidad puede estar sobreoptimista por segmento, no que todo odds alto sea inválido en cualquier contexto.

---

## Causa probable del problema en odds altas

Combinación de factores:
1. Mezcla de señales entre mercados (full-game y quarters no se comportan igual).
2. Sensibilidad a muestra/selección de picks entre dataset corto y ampliado.
3. En full-game, odds altas y algunos buckets intermedios muestran degradación de rendimiento pese a edge teórico.

---

## Policy temporal formal (vigente desde 2026-03-07 UTC)

### 1) Regla global
- **No aplicar prohibición global de >=2.0.**
- Aplicar policy **por mercado + bucket**.

### 2) Regla específica crítica
- **FULL-GAME >=2.0: BLOQUEADO temporalmente.**

### 3) Buckets intermedios peligrosos
- **FULL-GAME 1.6–1.8: RESTRINGIDO** (señal frágil/negativa).
- **Q3/Q4**: operar con sesgo conservador (mayor proporción de buckets negativos).

### 4) Buckets permitidos (con vigilancia)
- **FULL-GAME 1.8–2.0** y `<1.6`: permitidos, con monitoreo continuo.
- **Q1/Q2 1.8–2.0**: permitidos.
- `>=2.0` en Q1/Q2: **permitido con cautela** (no regla dura por estabilidad aún en construcción).

### 5) Criterio de muestra
- Si `n < 20` por bucket en ventana activa, no emitir regla dura: “permitido con cautela / muestra insuficiente”.

---

## Qué queda permitido / restringido / bloqueado

Ver matriz operativa oficial:
- `docs/borlty-context/MATRIZ_DE_POLICY_POR_ODDS_Y_MERCADO.md`

---

## Desde cuándo aplica

- **Desde:** 2026-03-07 (UTC)
- **Hasta:** próxima revisión de bloque 05 (o antes si se duplica muestra por bucket y cambia señal).

---

## Qué revisar cuando haya más muestra

1. Estabilidad de Q1/Q2 en `>=2.0`.
2. Si full-game 1.6–1.8 sigue frágil o mejora con mayor n.
3. Diferencia entre edge declarado y ROI realizado por bucket.
4. Relación de odds policy con confidence policy temporal.

---

## Cambio en código

- **No se aplicó cambio de código** en esta etapa.
- Decisión: documentar policy primero; cualquier guardrail en runtime se evalúa en el siguiente paso del bloque 05 con validación controlada.
