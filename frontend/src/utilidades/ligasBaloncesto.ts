/** La liga vive en la URL; recargar o compartir conserva el predictor elegido. */
export type LigaBaloncesto = 'nba' | 'euroliga' | 'wnba';

export function leerLigaBaloncesto(search: string): LigaBaloncesto {
  const liga = new URLSearchParams(search).get('liga');
  return liga === 'euroliga' || liga === 'wnba' ? liga : 'nba';
}

export function rutaBaloncesto(liga: LigaBaloncesto = 'nba'): string {
  return `/baloncesto?liga=${liga}`;
}
