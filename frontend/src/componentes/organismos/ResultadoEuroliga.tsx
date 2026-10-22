/** La salida Euro se presenta con el mismo organismo completo que NBA. */
import type { LadoApuesta } from '../../tipos';
import type { ResultadoEuro } from '../../servicios/euroliga';
import { adaptarResultadoEuroliga } from '../../utilidades/resultadoEuroliga';
import { ResultadoAnalisis } from './ResultadoAnalisis';

export function ResultadoEuroliga({ r, seleccionUsuario }: { r: ResultadoEuro; seleccionUsuario?: { lado: LadoApuesta; linea: number } | null }) {
  return <section aria-label="Resultado Euroliga"><ResultadoAnalisis resultado={adaptarResultadoEuroliga(r)} fuenteEuroliga={r} seleccionUsuario={seleccionUsuario} advertencias={r.advertencias} /></section>;
}
