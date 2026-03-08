# EXPLICABILIDAD_DEL_SISTEMA.md

Versión: v1  
Ámbito: Bloque 07.2 (Explicabilidad)  
Dependencias: Framework de calidad (reglas, scorecard, alertas)

> Objetivo: ofrecer explicaciones útiles para decidir **si apostar o no**, condicionadas por la calidad real de datos.  
> Límite: este modelo **no promete explicación perfecta**; entrega transparencia operativa bajo incertidumbre.

---

## 1. MODELO DE EXPLICACIÓN MÍNIMA

### 1.1 Componentes Obligatorios de Explicación

| Componente | Descripción | Formato | Obligatorio |
|------------|-------------|---------|-------------|
| Predicción | Valor numérico esperado (ej. total puntos/goles esperado o probabilidad de Over/Under) | Float | Sí |
| Confianza | Confianza del modelo ajustada por calidad | % + etiqueta cualitativa | Sí |
| Calidad Datos | Estado de calidad vigente al momento de inferencia | Score (0-100) + Nivel A/B/C | Sí |
| Top Factores | Principales impulsores de la predicción | Lista ordenada (Top 5) | Sí |
| Advertencias | Riesgos o limitaciones activas | Texto breve + severidad visual | Condicional |
| Contexto Histórico | Rendimiento en casos comparables | Stats resumidas | Opcional |

### 1.2 Lógica de Explicación por Nivel de Calidad

#### Datos Nivel A (90-100)
**Explicación estándar:**
- Predicción presentada como utilizable en operación normal.
- Mostrar top 5 factores contributivos.
- Confianza del modelo sin castigo adicional.
- Sin disclaimers técnicos extra (más allá del legal).

#### Datos Nivel B (70-89)
**Explicación con precaución:**
- Predicción presentada como utilizable con prudencia.
- Mostrar top 5 factores + advertencia de limitaciones detectadas.
- Confianza visual reducida a “Moderada” aunque el valor numérico sea alto.
- Disclaimer obligatorio: “Algunos datos presentan calidad reducida”.

#### Datos Nivel C (<70)
**Explicación con alerta fuerte:**
- No recomendar uso para decisiones de apuesta.
- Mostrar explícitamente qué componente(s) de datos están deficientes.
- Confianza marcada como “Baja / No confiable”.
- Disclaimer prominente: “ADVERTENCIA: Calidad de datos insuficiente”.

---

## 2. FACTORES EXPLICATIVOS

### 2.1 Taxonomía de Factores (NBA)

| Categoría | Ejemplos de Factores | Cómo se Calcula Contribución |
|-----------|----------------------|-------------------------------|
| Ofensiva del equipo | PPG, eFG%, 3P%, Pace | Coeficientes Ridge × valor estandarizado |
| Defensiva del equipo | Opp PPG, Defensive Rating, rebote defensivo | Coeficientes Ridge × valor estandarizado |
| Tendencias recientes | Últimos 5 juegos, variación ofensiva/defensiva | Pesos temporales + señal de momentum |
| Matchup específico | Head-to-head, estilo vs estilo | Interacciones de features / comparativo histórico |
| Contexto del juego | Home/Away, back-to-back, descanso | Coeficientes + ajustes de contexto |

### 2.2 Taxonomía de Factores (Fútbol)

| Categoría | Ejemplos de Factores | Cómo se Calcula Contribución |
|-----------|----------------------|-------------------------------|
| Producción ofensiva | xG a favor, tiros al arco, conversión | Coeficientes del modelo vigente × features normalizadas |
| Solidez defensiva | xGA, goles concedidos, duelos perdidos | Coeficientes + métricas de contención |
| Estado reciente | Forma últimos 5 partidos, tendencia Over/Under | Ventanas móviles + pesos recientes |
| Contexto competitivo | Localía, congestión de calendario, fatiga | Variables contextuales con peso específico |
| Condiciones de partido | Línea de mercado, volatilidad previa, competencia | Features de mercado/contexto + ajuste de incertidumbre |

### 2.3 Cálculo de Importancia

Regla base (Ridge):
1. Calcular contribución por feature: \(contrib_i = \beta_i \times x_i\) (sobre features estandarizadas).
2. Tomar magnitud absoluta: \(|contrib_i|\).
3. Normalizar a porcentaje:
\[
impacto_i(\%) = \frac{|contrib_i|}{\sum_j |contrib_j|} \times 100
\]
4. Ordenar por impacto absoluto y mostrar Top 5.
5. Mostrar dirección (↑ favorece Over / ↓ favorece Under) para legibilidad.

---

## 3. GESTIÓN DE INCERTIDUMBRE

### 3.1 Fuentes de Incertidumbre

| Fuente | Cómo se Mide | Cómo se Comunica |
|--------|---------------|------------------|
| Varianza del modelo | Intervalo de predicción / dispersión residual | Rango esperado (ej. 105-112) |
| Calidad de datos | Score y nivel A/B/C | Etiqueta de calidad visible |
| Drift detectado | Señal drift (yellow/orange/red) | Advertencia de patrón inusual |
| Coverage limitada | ratio cobertura / na_ratio | Disclaimer de datos parciales |

### 3.2 Comunicación de Confianza

No usar solo un número. Mostrar siempre:
1. **Intervalo de predicción** (rango numérico).
2. **Nivel cualitativo** (Alta / Moderada / Baja).
3. **Contexto histórico** (ej. precisión en casos similares).

Formato recomendado:
- `Confianza numérica:` 78%
- `Confianza cualitativa:` Moderada
- `Rango esperado:` 105–112
- `Contexto:` “En escenarios comparables, acierto histórico 74%”

---

## 4. ADVERTENCIAS Y DISCLAIMERS

### 4.1 Matriz de Advertencias

| Condición | Mensaje de Advertencia | Visibilidad |
|-----------|-------------------------|-------------|
| Calidad C | “ADVERTENCIA: Calidad de datos insuficiente” | Alta (rojo) |
| Drift detectado | “Patrón inusual detectado; resultados bajo revisión” | Media (amarillo) |
| Cobertura <80% | “Datos limitados disponibles para este escenario” | Media |
| Modelo en entrenamiento (Fútbol) | “Modelo en fase beta; interpretación conservadora” | Permanente |

### 4.2 Disclaimers Legales

Texto obligatorio en todas las predicciones:

> “Esta predicción es solo informativa y no constituye asesoría financiera.  
> Las apuestas deportivas implican riesgo. Solo debe apostar dinero que pueda permitirse perder.”

---

## 5. INTEGRACIÓN CON FRAMEWORK DE CALIDAD

### 5.1 Dependencias de Calidad

Antes de construir cualquier explicación:
1. Consultar `dq_scorecard_daily` (score + nivel A/B/C).
2. Consultar alertas activas (`data_quality_alerts`) del dominio/fuente.
3. Leer flags de calidad (`source_quality_flag`, `residual_warning`).

Regla operacional:
- Si nivel C -> modo de explicación restringida + advertencia fuerte.
- Si alertas críticas activas -> explicación con banner de riesgo.

### 5.2 Propagación de Flags

- `source_quality_flag` -> determina tono de explicación (normal / cautela / restringida).
- `residual_warning` -> agrega advertencias específicas (ej. drift o confidence temporal).
- `drift_alert` -> fuerza etiqueta “En revisión” en fútbol.

---

## 6. CASOS ESPECIALES

### 6.1 Drift Runtime (Fútbol)

Si drift detectado:
1. Marcar predicción como **“En revisión”**.
2. Explicar que existe patrón inusual de datos/contrato.
3. Rebajar confianza cualitativa en un nivel (Alta→Moderada, Moderada→Baja).
4. Recomendar precaución extrema en uso operativo.

### 6.2 Contratos Legacy

Durante coexistencia legacy/canónico:
1. La explicación debe mantener mismo contenido semántico en ambos contratos.
2. Incluir `contract_version` o `contract_mode` en metadatos (`canonical|legacy_compat`).
3. Si la salida viene de ruta legacy, añadir nota: “Salida en compatibilidad legacy; interpretación con cautela”.

---

## 7. SALIDA ESTÁNDAR DE EXPLICACIÓN (ESQUEMA)

```json
{
  "prediction_value": 0.64,
  "prediction_interval": [0.58, 0.69],
  "confidence_pct": 78,
  "confidence_label": "Moderada",
  "quality_score": 82,
  "quality_level": "B",
  "top_factors": [
    {"factor": "Offensive Rating local", "impact_pct": 24.3, "direction": "UP"},
    {"factor": "Pace reciente", "impact_pct": 18.1, "direction": "UP"},
    {"factor": "Defensive Rating rival", "impact_pct": 16.7, "direction": "DOWN"}
  ],
  "warnings": [
    "Algunos datos presentan calidad reducida"
  ],
  "historical_context": {
    "similar_cases_accuracy": 0.74,
    "sample_size": 186
  },
  "quality_flags": {
    "source_quality_flag": "B",
    "residual_warning": "confidence_temporal_policy_activa"
  },
  "legal_disclaimer": "Esta predicción es solo informativa y no constituye asesoría financiera. Las apuestas deportivas implican riesgo. Solo debe apostar dinero que pueda permitirse perder."
}
```

---

## Cierre

Este modelo de explicabilidad prioriza comprensión práctica, transparencia y control de riesgo.  
La explicación está condicionada por calidad real de datos, visibiliza limitaciones y evita sobreprometer confiabilidad cuando el sistema está degradado.
