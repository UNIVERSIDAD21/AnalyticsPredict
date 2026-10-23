/** Retorno por una unidad arriesgada. Push devuelve la unidad, beneficio cero. */
export function evaluarEscenario(p: number | null, perdida: number | null, push: number | null, cuota: number | null) {
  if (p === null || perdida === null || push === null || cuota === null || ![p, perdida, push, cuota].every(Number.isFinite)
    || cuota <= 1 || cuota > 1000 || Math.min(p, perdida, push) < 0 || Math.max(p, perdida, push) > 1
    || Math.abs(p + perdida + push - 1) > 0.001) return null;
  const ev = p * (cuota - 1) - perdida;
  return { ev, desviacionRetorno: Math.sqrt(Math.max(0, p * (cuota - 1) ** 2 + perdida - ev ** 2)),
    cuotaEquilibrio: p > 0 ? (1 - push) / p : null, probabilidadCondicional: push < 1 ? p / (1 - push) : null };
}
