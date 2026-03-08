import ExplicacionPrediccion from './ExplicacionPrediccion';
import { ContratoExplicacion } from '../../tipos/explicabilidad';

const base = {
  version: '1.0.0',
  prediction_id: 'demo-id',
  sport: 'NBA',
  market: 'over_under',
  game: { home_team: 'LAL', away_team: 'BOS', game_date: new Date().toISOString(), league: 'NBA' },
  prediction: {
    value: 112,
    unit: 'points',
    line: 108.5,
    recommendation: 'over',
    confidence: { level: 'high', numeric: 82, interval: { lower: 109, upper: 115 } },
  },
  data_quality: { score: 95, level: 'A', flags: [] },
  explanation: {
    top_factors: [
      { factor_name: 'offense', contribution: 45, value: 1, description: 'Ofensiva fuerte' },
      { factor_name: 'trend', contribution: 30, value: 1, description: 'Tendencia reciente' },
    ],
    warnings: [],
    historical_context: { similar_predictions: 150, accuracy_rate: 0.74, sample_size: 150 },
  },
  metadata: { model_version: 'demo', generated_at: new Date().toISOString(), backend_version: 'demo', is_legacy_contract: false, debt_flags: [] },
} as const satisfies ContratoExplicacion;

const demoA: ContratoExplicacion = base;
const demoB: ContratoExplicacion = {
  ...base,
  sport: 'FOOTBALL',
  prediction: { ...base.prediction, unit: 'goals', value: 2.5, line: 3.0, confidence: { ...base.prediction.confidence, level: 'high', numeric: 79 } },
  data_quality: { score: 78, level: 'B', flags: [{ type: 'coverage', severity: 'medium', message: 'Cobertura 75%' }] },
  explanation: { ...base.explanation, warnings: [{ type: 'coverage', message: 'Datos limitados', severity: 'medium' }] },
  metadata: { ...base.metadata, debt_flags: ['confidence_parcial_bloque_05'] },
};
const demoC: ContratoExplicacion = {
  ...base,
  sport: 'FOOTBALL',
  prediction: { ...base.prediction, recommendation: 'skip', confidence: { ...base.prediction.confidence, level: 'low', numeric: 42 } },
  data_quality: { score: 62, level: 'C', flags: [{ type: 'drift', severity: 'critical', message: 'Drift rojo' }] },
  explanation: { ...base.explanation, warnings: [{ type: 'drift', message: 'Patrón inusual detectado', severity: 'high' }] },
  metadata: { ...base.metadata, is_legacy_contract: true, debt_flags: ['drift_futbol_parcial_alto_bloque_05', 'confidence_parcial_bloque_05'] },
};

/** Demo local de los 3 flujos A/B/C */
export default function ExplicacionDemo() {
  return (
    <div className="space-y-6">
      <ExplicacionPrediccion predictionId="demo-a" fallbackData={demoA} />
      <ExplicacionPrediccion predictionId="demo-b" fallbackData={demoB} />
      <ExplicacionPrediccion predictionId="demo-c" fallbackData={demoC} />
    </div>
  );
}
