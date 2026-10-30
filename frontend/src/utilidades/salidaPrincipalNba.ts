import type { ResultadoVista } from '../tipos/resultadoVista';
const numero = (n: unknown): number | null => typeof n === 'number' && Number.isFinite(n) ? n : null;
const prob = (n: unknown) => { const v = numero(n); return v !== null && v >= 0 && v <= 1 ? v : null; };
/** Un único origen para media/sigma/p. No usa candidato, cuota ni escenario ajustado. */
export function salidaPrincipalNba(r: ResultadoVista, mercado: string, linea: number) {
  const p = mercado === 'COMPLETO' ? r.prediccion_juego_completo : r.predicciones[mercado];
  const original = numero(p?.linea_analizada) ?? numero(r.linea_analizada);
  const compatible = Number.isFinite(linea) && Math.abs(linea % 1 - .5) < 1e-9;
  const coincide = original !== null && Math.abs(original - linea) < 1e-9;
  const motivo = !compatible ? 'Línea entera/fraccionaria: probabilidad del evento discreto y push N/D. La normal continua no conserva esa masa.' : !coincide ? 'La línea de esta selección no coincide con la calculada. Probabilidades N/D; conserva la selección original o realiza una nueva consulta explícita.' : null;
  return { media: numero(p?.media_total), desviacion: numero(p?.desviacion_total),
    over: motivo ? null : prob(p?.probabilidad_over), under: motivo ? null : prob(p?.probabilidad_under),
    push: compatible && coincide ? 0 : null, motivo,
    origen: r.es_en_vivo ? 'Corte NBA · RAW, heurística de cierre sin reloj ni posesiones' : 'Base NBA · RAW, sin ajuste contextual adicional',
  };
}
