export type Sport = 'NBA' | 'FOOTBALL';
export type MarketType = 'over_under';
export type PredictionUnit = 'points' | 'goals';
export type Recommendation = 'over' | 'under' | 'skip';
export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type QualityLevel = 'A' | 'B' | 'C';

export type QualityFlagType =
  | 'drift'
  | 'incomplete'
  | 'stale'
  | 'outlier'
  | 'quality'
  | 'coverage'
  | 'beta';

export type FlagSeverity = 'critical' | 'high' | 'medium' | 'low';

export type WarningType =
  | 'quality'
  | 'drift'
  | 'coverage'
  | 'beta'
  | 'stale'
  | 'outlier'
  | 'incomplete';

export type WarningSeverity = 'high' | 'medium' | 'low';

export interface PredictionInterval {
  lower: number;
  upper: number;
}

export interface PredictionConfidence {
  level: ConfidenceLevel;
  numeric: number; // 0..100
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
  score: number;
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
  generated_at: string;
  backend_version: string;
  is_legacy_contract: boolean;
  debt_flags: string[];
  [key: string]: unknown;
}

export interface ContratoExplicacion {
  version: string;
  prediction_id: string;
  sport: Sport;
  market: MarketType;
  game: GameInfo;
  prediction: PredictionPayload;
  data_quality: DataQuality;
  explanation: ExplanationPayload;
  metadata: PredictionMetadata;
}
