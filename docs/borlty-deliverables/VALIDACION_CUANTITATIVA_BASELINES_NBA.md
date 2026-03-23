# VALIDACION_CUANTITATIVA_BASELINES_NBA.md

## Objetivo
Validar cuantitativamente en BD real los baselines:
- Win rate NBA 81.48%
- ROI NBA 11.53%
- Confidence paradox (HIGH/ALTA peor que MEDIUM/LOW)
- Desempeño de odds > 2.0
- Quarter markets vs full-game

## Estado de ejecución
**Estado:** EJECUTADO EN BD REAL (cerrado con evidencia)

### Ejecución reproducible
- Comando:
  - `python scripts/validar_baselines_nba.py --inicio 2024-01-01 --fin 2026-12-31`
- Salida generada:
  - `reports/auditoria_baselines/baseline_nba_2024-01-01_2026-12-31_20260307T002134Z.json`

---

## Fuente canónica elegida y justificación

### Fuente canónica
**Tabla:** `apuestas` (NBA)

### Por qué esta fuente
Se eligió `apuestas` porque concentra las dimensiones necesarias para los baselines solicitados:
- `resultado` (GANADA/PERDIDA/PUSH)
- `stake`, `ganancia` (para ROI)
- `confianza_sistema` (paradoja de confidence)
- `cuota` (segmentación odds > 2.0)
- `mercado` (Q1..Q4 vs COMPLETO)
- `fecha_partido/creado_en` (rango temporal)

No se usó inferencia desde dashboard ni documentos históricos.

---

## Definiciones métricas (supuestos explícitos)

1. **Win rate (%)**
- Numerador: `GANADA`
- Denominador: `GANADA + PERDIDA`
- `PUSH` se excluye del win/loss.

2. **ROI (%)**
- `SUM(ganancia) / SUM(stake) * 100`
- Universo ROI: `GANADA + PERDIDA + PUSH`

3. **Confidence paradox**
- Segmentación por `UPPER(confianza_sistema)` (ALTA/MEDIA/BAJA/SIN_DATO)
- Comparación principal por ROI y win rate por segmento.

4. **Odds > 2.0**
- Segmentos: `cuota > 2.0` vs `cuota <= 2.0`
- Comparación por ROI y win rate.

5. **Quarter vs Full-game**
- `QUARTER_MARKETS`: mercado IN (`Q1`,`Q2`,`Q3`,`Q4`)
- `FULL_GAME_MARKETS`: mercado IN (`COMPLETO`,`FULL`,`FULL_GAME`)

---

## Rango temporal solicitado para ejecución

- Inicio: `2024-01-01`
- Fin: `2026-12-31`

> Nota: el rango está parametrizado y puede ajustarse; aún no hay resultados por bloqueo de credenciales.

---

## Queries SQL exactas usadas

Archivo canónico:
- `docs/borlty-context/sql/BASELINES_VALIDACION_NBA.sql`

Incluye:
- Query universo y muestra efectiva
- Query global (win rate + ROI)
- Query confidence segmentada
- Query odds segmentada
- Query quarter vs full-game

---

## Ejecutor reproducible

Se creó script reproducible:
- `backend/scripts/validar_baselines_nba.py`

### Comando
```bash
cd backend
. .venv/bin/activate
python scripts/validar_baselines_nba.py --inicio 2024-01-01 --fin 2026-12-31
```

### Salida esperada (si hay credenciales)
- JSON en: `reports/auditoria_baselines/baseline_nba_<inicio>_<fin>_<timestamp>.json`

---

## Rango temporal y universo efectivo analizado

- Rango solicitado: **2024-01-01 → 2026-12-31**
- Rango efectivo en datos: **2026-01-10 → 2026-02-22**
- Universo total: **144** apuestas
- Universo resuelto (GANADA/PERDIDA/PUSH): **129**

---

## Resultados numéricos

### Global NBA
- `n_resueltas`: 129
- `n_ganadas`: 100
- `win_rate_pct`: **77.5194%**
- `roi_pct`: **-1.0974%**
- `stake_total`: 195,064.00
- `ganancia_total`: -2,140.71

### Confidence (segmentado)
- ALTA: n=54, win_rate=83.3333%, ROI=16.9618%
- MEDIA: n=43, win_rate=83.7209%, ROI=26.0943%
- BAJA: n=32, win_rate=59.3750%, ROI=-65.7300%

### Odds segmentado
- ODDS_GT_2_0: n=5, win_rate=20.0000%, ROI=-137.3800%
- ODDS_LE_2_0: n=124, win_rate=79.8387%, ROI=2.4877%

### Tipo de mercado
- FULL_GAME_MARKETS: n=97, win_rate=77.3196%, ROI=-5.2158%
- QUARTER_MARKETS: n=32, win_rate=78.1250%, ROI=19.8888%

---

## Tamaño de muestra por segmento

- Global resueltas: n=129
- Confidence: ALTA n=54, MEDIA n=43, BAJA n=32
- Odds: >2.0 n=5, <=2.0 n=124
- Mercados: Quarter n=32, Full-game n=97

---

## Veredicto por baseline

| Baseline | Veredicto | Evidencia |
|---|---|---|
| Win rate NBA 81.48% | **REFUTADO** | Observado 77.5194% |
| ROI NBA 11.53% | **REFUTADO** | Observado -1.0974% |
| Confidence paradox | **INCONCLUSO** | ALTA rinde peor que MEDIA (sí), pero mejor que BAJA (no cumple “peor que MEDIUM/LOW” de forma completa) |
| Odds > 2.0 con rendimiento muy negativo | **CONFIRMADO** | ROI -137.38% (n=5; muestra pequeña) |
| Quarter markets mejores que full-game | **CONFIRMADO** | ROI Quarter 19.8888% vs Full-game -5.2158% |

---

## Bloqueos reales / limitaciones

1. El baseline de odds > 2.0 se confirma con **muestra baja (n=5)**; se recomienda seguir monitoreo y no sobreajustar por tamaño muestral.
2. El rango efectivo con datos cae en 2026-01-10 a 2026-02-22; para inferencia más robusta conviene ampliar histórico útil si existe fuera de `apuestas`.

---

## Conclusión operativa

La foto actual de BD **refuta** los baselines históricos globales (81.48% / 11.53%) y confirma dos reglas operativas relevantes:
- evitar/exigir cautela extrema en odds > 2.0,
- priorizar quarter markets sobre full-game en estado actual.

---

## Nota de alcance

No se aplicó refactor masivo, ni cambios de arquitectura/modelos/chatbot en esta etapa.
Se mantuvo alcance estricto en validación cuantitativa y reproducibilidad.
