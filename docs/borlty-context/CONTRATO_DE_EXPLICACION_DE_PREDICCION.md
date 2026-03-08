# CONTRATO_DE_EXPLICACION_DE_PREDICCION.md

Versión del documento: 1.0  
Ámbito: Contrato backend ↔ frontend para explicación de predicciones (Bloque 07.2)  
Dependencias: `EXPLICABILIDAD_DEL_SISTEMA.md`, framework de calidad (reglas/scorecard/alertas)

---

## 1. SCHEMA DEL CONTRATO

### 1.1 Schema JSON v1.0

```json
{
  "version": "1.0.0",
  "prediction_id": "uuid",
  "sport": "NBA",
  "market": "over_under",
  "game": {
    "home_team": "string",
    "away_team": "string",
    "game_date": "2026-03-08T22:00:00Z",
    "league": "NBA"
  },
  "prediction": {
    "value": 214.5,
    "unit": "points",
    "line": 212.5,
    "recommendation": "over",
    "confidence": {
      "level": "high",
      "numeric": 82,
      "interval": {
        "lower": 208.0,
        "upper": 220.3
      }
    }
  },
  "data_quality": {
    "score": 93,
    "level": "A",
    "flags": [
      {
        "type": "outlier",
        "severity": "medium",
        "message": "Outlier rate controlado dentro de umbral permitido"
      }
    ]
  },
  "explanation": {
    "top_factors": [
      {
        "factor_name": "offensive_rating_home",
        "contribution": 21.3,
        "value": 114.2,
        "description": "Ofensiva local por encima del promedio"
      }
    ],
    "warnings": [
      {
        "type": "quality",
        "message": "Sin advertencias críticas activas",
        "severity": "low"
      }
    ],
    "historical_context": {
      "similar_predictions": 248,
      "accuracy_rate": 0.74,
      "sample_size": 248
    }
  },
  "metadata": {
    "model_version": "ridge_nba_v3.2.1",
    "generated_at": "2026-03-08T22:50:00Z",
    "backend_version": "api-2.9.0",
    "is_legacy_contract": false
  }
}
```

> Nota de normalización:
- `sport` permitido: `NBA | FOOTBALL` (en contrato de API pública).  
- Internamente puede existir `FUTBOL`; se transforma a `FOOTBALL` para evitar ambigüedad de consumidores externos.

### 1.2 Tipos TypeScript

```typescript
export type Sport = 'NBA' | 'FOOTBALL';
export type MarketType = 'over_under';
export type PredictionUnit = 'points' | 'goals';
export type Recommendation = 'over' | 'under' | 'skip';
export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type QualityLevel = 'A' | 'B' | 'C';

export type QualityFlagType = 'drift' | 'incomplete' | 'stale' | 'outlier';
export type FlagSeverity = 'critical' | 'high' | 'medium';

export type WarningType = 'quality' | 'drift' | 'coverage' | 'beta';
export type WarningSeverity = 'high' | 'medium' | 'low';

export interface PredictionInterval {
  lower: number;
  upper: number;
}

export interface PredictionConfidence {
  level: ConfidenceLevel;
  numeric: number; // 0-100
  interval: PredictionInterval;
}

export interface PredictionPayload {
  value: number;
  unit: PredictionUnit;
  line: number;
  recommendation: Recommendation;
  confidence: PredictionConfidence;
}

export interface GameInfo {
  home_team: string;
  away_team: string;
  game_date: string; // ISO8601
  league: string;
}

export interface DataQualityFlag {
  type: QualityFlagType;
  severity: FlagSeverity;
  message: string;
}

export interface DataQuality {
  score: number; // 0-100
  level: QualityLevel;
  flags: DataQualityFlag[];
}

export interface TopFactor {
  factor_name: string;
  contribution: number; // -100..100
  value: number;
  description: string;
}

export interface ExplanationWarning {
  type: WarningType;
  message: string;
  severity: WarningSeverity;
}

export interface HistoricalContext {
  similar_predictions: number;
  accuracy_rate: number; // 0..1
  sample_size: number;
}

export interface ExplanationPayload {
  top_factors: TopFactor[];
  warnings: ExplanationWarning[];
  historical_context?: HistoricalContext;
}

export interface PredictionMetadata {
  model_version: string;
  generated_at: string; // ISO8601
  backend_version: string;
  is_legacy_contract: boolean;
}

export interface PredictionExplanation {
  version: string; // semver
  prediction_id: string; // uuid
  sport: Sport;
  market: MarketType;
  game: GameInfo;
  prediction: PredictionPayload;
  data_quality: DataQuality;
  explanation: ExplanationPayload;
  metadata: PredictionMetadata;
}
```

---

## 2. VERSIONAMIENTO

### 2.1 Política de Versiones

Se adopta **Semantic Versioning (MAJOR.MINOR.PATCH)**:
- **MAJOR:** cambio breaking (renombrar/eliminar campos obligatorios, cambio de tipos/enums incompatibles).
- **MINOR:** adición retrocompatible (campos opcionales, nuevos warning types, extensiones de metadata).
- **PATCH:** correcciones internas sin impacto contractual.

### 2.2 Evolución del Contrato

| Versión | Cambios | Retrocompatible | Fecha |
|---------|---------|-----------------|-------|
| 1.0.0 | Release inicial del contrato canónico de explicación | N/A | 2026-03-08 |
| 1.1.0 | Agregar `ensemble_components` en `metadata` o `explanation` | Sí | Futura |
| 2.0.0 | Reestructura de `confidence` o `top_factors` con breaking changes | No | Futura |

### 2.3 Deprecation Policy

1. Mínimo **2 versiones simultáneas** en solapamiento (ej. v1 y v2).
2. Si un cliente consume versión deprecated, responder con:
   - header `X-Contract-Deprecated: true`
   - campo opcional `metadata.deprecation_notice`.
3. Comunicar `sunset_date` con **90 días** de anticipación.
4. Pasado sunset, versión vieja entra en modo `legacy_compat` con SLA reducido o se retira según política operativa.

---

## 3. COMPATIBILIDAD CON CONTRATOS LEGACY

### 3.1 Mapeo Legacy → Nuevo

| Campo Legacy | Campo Nuevo | Transformación | Notas |
|--------------|-------------|----------------|-------|
| `id` | `prediction_id` | copia directa / cast uuid string | obligatorio |
| `deporte` (`NBA`,`FUTBOL`) | `sport` (`NBA`,`FOOTBALL`) | map enum (`FUTBOL`→`FOOTBALL`) | normalización pública |
| `mercado` | `market` | map a `over_under` | v1 solo over_under |
| `equipo_local`/`equipo_visitante` | `game.home_team`/`game.away_team` | copia directa | |
| `fecha_partido` | `game.game_date` | parse a ISO8601 | timezone UTC |
| `valor_predicho` | `prediction.value` | numérico | |
| `linea` | `prediction.line` | numérico | |
| `recomendacion` | `prediction.recommendation` | map enum (`OVER`,`UNDER`,`SKIP`) | case-insensitive |
| `confianza`/`probabilidad` | `prediction.confidence.numeric` | normalizar a 0-100 | si viene 0-1, multiplicar x100 |
| `calidad_score` | `data_quality.score` | numérico 0-100 | |
| `calidad_nivel` | `data_quality.level` | enum A/B/C | |
| `warning_*` | `explanation.warnings[]` | agrupar array tipado | |
| `modelo` | `metadata.model_version` | copia | |
| `legacy=true` | `metadata.is_legacy_contract` | copia bool | obligatorio para trazabilidad |

### 3.2 Período de Coexistencia

- Contrato legacy y nuevo disponibles en paralelo.
- `metadata.is_legacy_contract` identifica origen.
- Migración gradual por consumidor (web, mobile, API partners).

### 3.3 Endpoint Legacy

`GET /api/v1/predictions/{id}/explanation?contract_version=legacy`

### 3.4 Endpoint Nuevo

`GET /api/v2/predictions/{id}/explanation`

---

## 4. VALIDACIÓN Y TESTING

### 4.1 Schema Validation

- Validación runtime con **JSON Schema Draft 2020-12**.
- Archivo sugerido: `schemas/prediction-explanation.v1.0.0.schema.json`.
- Validación en backend antes de responder y en frontend durante integración (modo dev/test).

JSON Schema base (resumen):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://analyticspredict/schemas/prediction-explanation.v1.0.0.schema.json",
  "type": "object",
  "required": [
    "version","prediction_id","sport","market","game","prediction",
    "data_quality","explanation","metadata"
  ],
  "properties": {
    "version": { "type": "string", "pattern": "^1\\.0\\.0$" },
    "prediction_id": { "type": "string", "format": "uuid" },
    "sport": { "type": "string", "enum": ["NBA", "FOOTBALL"] },
    "market": { "type": "string", "enum": ["over_under"] }
  },
  "additionalProperties": false
}
```

### 4.2 Test Cases Obligatorios

| Test Case | Descripción | Resultado Esperado |
|-----------|-------------|-------------------|
| Valid Prediction A | Datos nivel A | Schema válido, warnings no críticos |
| Valid Prediction B | Datos nivel B | Schema válido, warnings moderados |
| Invalid Quality C | Datos nivel C | Schema válido, warning crítico y recomendación `skip` o cautela extrema |
| Drift Detection | Drift activo | `data_quality.flags` incluye `type=drift` |
| Legacy Contract | Contrato legacy | `metadata.is_legacy_contract=true` y mapping correcto |

### 4.3 Ejemplos de Responses

#### Ejemplo 1: Predicción normal, calidad A

```json
{
  "version": "1.0.0",
  "prediction_id": "58d648d6-b9b6-4d46-9c5b-c3427b5b4cc8",
  "sport": "NBA",
  "market": "over_under",
  "game": {
    "home_team": "Boston Celtics",
    "away_team": "Miami Heat",
    "game_date": "2026-03-10T00:30:00Z",
    "league": "NBA"
  },
  "prediction": {
    "value": 221.4,
    "unit": "points",
    "line": 218.5,
    "recommendation": "over",
    "confidence": {
      "level": "high",
      "numeric": 84,
      "interval": { "lower": 215.2, "upper": 226.9 }
    }
  },
  "data_quality": {
    "score": 94,
    "level": "A",
    "flags": []
  },
  "explanation": {
    "top_factors": [
      { "factor_name": "pace_recent", "contribution": 23.4, "value": 101.8, "description": "Ritmo alto reciente" },
      { "factor_name": "off_rating_home", "contribution": 18.9, "value": 117.1, "description": "Ofensiva local fuerte" }
    ],
    "warnings": [],
    "historical_context": {
      "similar_predictions": 312,
      "accuracy_rate": 0.76,
      "sample_size": 312
    }
  },
  "metadata": {
    "model_version": "ridge_nba_v3.2.1",
    "generated_at": "2026-03-08T22:50:00Z",
    "backend_version": "api-2.9.0",
    "is_legacy_contract": false
  }
}
```

#### Ejemplo 2: Predicción con warnings, calidad B

```json
{
  "version": "1.0.0",
  "prediction_id": "46a7f7f7-6f4b-4f52-8fa2-1ee7d897bcd1",
  "sport": "FOOTBALL",
  "market": "over_under",
  "game": {
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "game_date": "2026-03-12T19:00:00Z",
    "league": "Premier League"
  },
  "prediction": {
    "value": 2.7,
    "unit": "goals",
    "line": 2.5,
    "recommendation": "over",
    "confidence": {
      "level": "medium",
      "numeric": 68,
      "interval": { "lower": 2.1, "upper": 3.2 }
    }
  },
  "data_quality": {
    "score": 78,
    "level": "B",
    "flags": [
      { "type": "coverage", "severity": "medium", "message": "Cobertura limitada para este mercado" },
      { "type": "drift", "severity": "high", "message": "Patrón inusual detectado en runtime" }
    ]
  },
  "explanation": {
    "top_factors": [
      { "factor_name": "xg_home_recent", "contribution": 19.4, "value": 1.86, "description": "xG local estable al alza" },
      { "factor_name": "xga_away_recent", "contribution": 16.7, "value": 1.42, "description": "Concesión rival elevada" }
    ],
    "warnings": [
      { "type": "quality", "message": "Algunos datos presentan calidad reducida", "severity": "medium" },
      { "type": "drift", "message": "Drift activo, usar con cautela", "severity": "high" }
    ],
    "historical_context": {
      "similar_predictions": 128,
      "accuracy_rate": 0.69,
      "sample_size": 128
    }
  },
  "metadata": {
    "model_version": "football_beta_v1.4.0",
    "generated_at": "2026-03-08T22:50:00Z",
    "backend_version": "api-2.9.0",
    "is_legacy_contract": false
  }
}
```

#### Ejemplo 3: Predicción nivel C con alertas

```json
{
  "version": "1.0.0",
  "prediction_id": "e6803459-5140-4525-aa0b-a1842e58f4ea",
  "sport": "FOOTBALL",
  "market": "over_under",
  "game": {
    "home_team": "Valencia",
    "away_team": "Sevilla",
    "game_date": "2026-03-13T20:00:00Z",
    "league": "LaLiga"
  },
  "prediction": {
    "value": 2.3,
    "unit": "goals",
    "line": 2.5,
    "recommendation": "skip",
    "confidence": {
      "level": "low",
      "numeric": 41,
      "interval": { "lower": 1.6, "upper": 3.1 }
    }
  },
  "data_quality": {
    "score": 62,
    "level": "C",
    "flags": [
      { "type": "drift", "severity": "critical", "message": "Drift runtime fútbol en nivel rojo" },
      { "type": "stale", "severity": "high", "message": "Freshness excede umbral operativo" },
      { "type": "incomplete", "severity": "high", "message": "Campos críticos incompletos" }
    ]
  },
  "explanation": {
    "top_factors": [
      { "factor_name": "form_recent", "contribution": 14.0, "value": 0.52, "description": "Señal débil por datos parciales" }
    ],
    "warnings": [
      { "type": "quality", "message": "ADVERTENCIA: Calidad de datos insuficiente", "severity": "high" },
      { "type": "drift", "message": "Predicción en revisión por drift activo", "severity": "high" },
      { "type": "beta", "message": "Modelo fútbol en fase beta", "severity": "medium" }
    ],
    "historical_context": {
      "similar_predictions": 74,
      "accuracy_rate": 0.61,
      "sample_size": 74
    }
  },
  "metadata": {
    "model_version": "football_beta_v1.4.0",
    "generated_at": "2026-03-08T22:50:00Z",
    "backend_version": "api-2.9.0",
    "is_legacy_contract": true
  }
}
```

---

## 5. DOCUMENTACIÓN PARA CONSUMIDORES

### 5.1 Guía de Integración Frontend

1. Consumir endpoint v2 y validar `version`.
2. Parsear `data_quality.level` para UI condicional:
   - A: vista normal
   - B: vista con warning moderado
   - C: bloquear CTA principal y mostrar alerta fuerte
3. Renderizar `explanation.top_factors` (Top 5 máximo).
4. Renderizar `warnings` por severidad visual.
5. Fallback de errores:
   - schema inválido -> mostrar mensaje técnico y no renderizar recomendación.
   - timeouts -> usar retry exponencial + estado “explicación no disponible”.

### 5.2 Guía de Integración API Externa

- **Rate limits recomendados:** 60 req/min por token (burst 120).
- **Authentication:** Bearer token (JWT/API key según gateway).
- **Caching:**
  - TTL sugerido: 60s para predicción en vivo, 5min para históricas.
  - usar `ETag`/`If-None-Match` para eficiencia.
- **Idempotencia de lectura:** GET seguro, sin efectos colaterales.

---

## 6. GARANTÍAS Y LIMITACIONES

### 6.1 Garantías del Contrato

- ✓ Schema siempre válido para respuestas exitosas (2xx).
- ✓ Campos obligatorios presentes según versión.
- ✓ Enums con valores definidos y documentados.
- ✓ Versionamiento explícito (`version`) en cada payload.
- ✓ Trazabilidad de origen (`metadata.is_legacy_contract`).

### 6.2 Limitaciones Conocidas

- ✗ No garantiza precisión de predicción.
- ✗ No garantiza disponibilidad 100% del servicio.
- ✗ Latencia puede variar según volumen/calidad de datos y estado de alertas.
- ✗ En modo legacy_compat pueden existir diferencias menores de granularidad.

---

## Cierre

Este contrato establece una base canónica, versionable y extensible para explicaciones de predicción, con compatibilidad controlada para legado y consumo estable en React/TypeScript, mobile y APIs externas.
