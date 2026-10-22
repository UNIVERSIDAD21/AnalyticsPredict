/** La liga vive en la URL; recargar o compartir conserva el predictor elegido. */
export type LigaBaloncesto = 'nba' | 'euroliga';

export function leerLigaBaloncesto(search: string): LigaBaloncesto {
  return new URLSearchParams(search).get('liga') === 'euroliga' ? 'euroliga' : 'nba';
}

export function rutaBaloncesto(liga: LigaBaloncesto = 'nba'): string {
  return `/baloncesto?liga=${liga}`;
}
