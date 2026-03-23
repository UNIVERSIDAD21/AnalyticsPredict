# Contrato de API — Analizador NBA v2.0

## Campos de Request

### Mercado 2-way (Over/Under)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| cuota_over | float | ❌ | Cuota decimal para OVER (>1.0) |
| cuota_under | float | ❌ | Cuota decimal para UNDER (>1.0) |
| cuota | float | ❌ | [LEGACY] Cuota del lado indicado |

### Reglas de Precedencia

1. Si llegan `cuota_over` + `cuota_under` → Se ignora `cuota`.
2. Si solo llega `cuota` → Se asigna al lado indicado, devig según `modo_devig`.
3. Si no hay cuotas → Solo predicción, sin análisis de mercado.

### Money Management

| Campo | Tipo | Default | Valores |
|-------|------|---------|---------|
| bankroll | float | null | >0 |
| perfil_riesgo | string | "CONSERVADOR" | CONSERVADOR, MEDIO, AGRESIVO |
| modo_devig | string | "estricto" | estricto, estimado |

---

## Ejemplos Narrativos

### Escenario 1: De-vig Exacto (ambas cuotas)

**Request:**
```json
{
  "equipo_local": "Los Angeles Lakers",
  "equipo_visitante": "Miami Heat",
  "mercado": "Q1",
  "linea": 50.5,
  "cuota_over": 1.91,
  "cuota_under": 1.91,
  "lado": "OVER",
  "bankroll": 1000,
  "perfil_riesgo": "MEDIO"
}
```

**Response (extracto mejor_apuesta):**
```json
{
  "mejor_apuesta": {
    "lado": "OVER",
    "linea": 50.5,
    "cuota": 1.91,
    "probabilidad_sistema": 0.55,
    "devig_metodo": "exacto",
    "devig_overround": 1.047,
    "devig_p_mkt_raw": 0.524,
    "devig_p_mkt_fair": 0.50,
    "edge_real": 0.05,
    "valor_esperado": 0.05,
    "score_total": 7.5,
    "kelly_full": 0.10,
    "kelly_fraccional": 0.025,
    "stake": 25.0,
    "stake_porcentaje": 2.5
  },
  "advertencias": []
}
```

### Escenario 2: Una cuota, modo estricto

**Request:**
```json
{
  "equipo_local": "Lakers",
  "equipo_visitante": "Heat",
  "mercado": "Q1",
  "linea": 50.5,
  "cuota_over": 1.85,
  "lado": "OVER",
  "modo_devig": "estricto"
}
```

**Response:**
```json
{
  "mejor_apuesta": {
    "devig_metodo": "no_aplicado",
    "devig_p_mkt_raw": 0.54,
    "devig_p_mkt_fair": 0.54,
    "edge_real": 0.01,
    "score_total": -1000.0,
    "score_explicacion": "Score=-1000 [NO APTO: gates]"
  },
  "advertencias": ["DEVIG_ESTRICTO_REQUIERE_AMBAS_CUOTAS"]
}
```

### Escenario 3: Una cuota, modo estimado

**Request:**
```json
{
  "equipo_local": "Lakers",
  "equipo_visitante": "Heat",
  "mercado": "Q1",
  "linea": 50.5,
  "cuota_over": 1.85,
  "lado": "OVER",
  "modo_devig": "estimado",
  "bankroll": 1000
}
```

**Response:**
```json
{
  "mejor_apuesta": {
    "devig_metodo": "estimado",
    "devig_overround": 1.045,
    "devig_p_mkt_raw": 0.54,
    "devig_p_mkt_fair": 0.517,
    "score_penalizaciones": ["DEVIG_ESTIMADO"],
    "kelly_fraccional": 0.0125,
    "sizing_penalizaciones": {"devig_estimado": 0.5}
  },
  "advertencias": ["DEVIG_ESTIMADO_PENALIZA"]
}
```

### Escenario 4: Sin apuestas aptas (EV negativo)

**Response:**
```json
{
  "mejor_apuesta": null,
  "mensaje_apuesta": "NO_APTO: EV<=0 o edge_real<=0 en todos los candidatos",
  "candidatos": [
    {
      "lado": "OVER",
      "ev": -0.02,
      "edge_real": -0.03,
      "score_total": -1000.0,
      "score_explicacion": "[NO APTO: gates]"
    }
  ]
}
```

---

## Códigos de Advertencia

| Código | Significado | Acción |
|--------|-------------|--------|
| DEVIG_ESTRICTO_REQUIERE_AMBAS_CUOTAS | Solo una cuota en modo estricto | Enviar ambas cuotas o cambiar a estimado |
| DEVIG_ESTIMADO_PENALIZA | De-vig aproximado | Stake reducido 50% |
| OVERROUND_ALTO_REVISAR | Overround > 1.10 | Verificar cuotas |
| OVERROUND_BAJO_POSIBLE_ARB | Overround < 1.0 | Posible arbitraje |
