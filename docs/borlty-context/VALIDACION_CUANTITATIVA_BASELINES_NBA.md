# VALIDACION_CUANTITATIVA_BASELINES_NBA.md

## Objetivo
Validar cuantitativamente en BD real los baselines:
- Win rate NBA 81.48%
- ROI NBA 11.53%
- Confidence paradox (HIGH/ALTA peor que MEDIUM/LOW)
- Desempeño de odds > 2.0
- Quarter markets vs full-game

## Estado de ejecución
**Estado:** BLOQUEADO (inconcluso)

Se preparó y ejecutó pipeline reproducible de validación, pero la ejecución contra BD real quedó bloqueada por credenciales no disponibles en entorno local.

### Bloqueo real observado
- `DATABASE_URL` no configurada en `.env` ni variables de entorno.
- Evidencia de ejecución:
  - Comando: `python scripts/validar_baselines_nba.py --inicio 2024-01-01 --fin 2026-12-31`
  - Error: `RuntimeError: DATABASE_URL no configurada en entorno/.env`

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

## Tamaño de muestra por segmento

**No disponible (bloqueado):** requiere conexión exitosa a BD para calcular `n_resueltas`, `n_winloss`, `stake_total` y `ganancia_total` por segmento.

---

## Veredicto por baseline

| Baseline | Veredicto | Justificación |
|---|---|---|
| Win rate NBA 81.48% | INCONCLUSO | No se pudo ejecutar query en BD real |
| ROI NBA 11.53% | INCONCLUSO | No se pudo ejecutar query en BD real |
| Confidence paradox | INCONCLUSO | No se pudo segmentar por `confianza_sistema` |
| Odds > 2.0 negativo | INCONCLUSO | No se pudo segmentar por `cuota` |
| Quarter > full-game | INCONCLUSO | No se pudo segmentar por `mercado` |

---

## Próximo paso inmediato para desbloquear

1. Cargar `DATABASE_URL` real (Neon) en:
   - `backend/.env` o variable de entorno del shell.
2. Re-ejecutar script de validación.
3. Generar versión final con resultados numéricos y veredictos confirmados/refutados.

---

## Nota de alcance

No se aplicó refactor masivo, ni cambios de arquitectura/modelos/chatbot en esta etapa.
Se mantuvo alcance estricto en validación cuantitativa y reproducibilidad.
