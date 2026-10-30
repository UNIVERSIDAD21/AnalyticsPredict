/** Duración del objetivo seleccionado, no de otro mercado de la misma respuesta. */
export function alcanceConsulta(metadata: Record<string, unknown>, mercado: string) {
  if (metadata.deporte === 'futbol') return '90 minutos más añadido; sin prórroga ni penales';
  if (metadata.liga === 'euroliga') return '40 minutos de regulación, sin OT · RAW';
  if (metadata.liga === 'wnba') return /^Q[1-4]$/.test(mercado) ? 'Cuarto de 10 minutos, sin OT · SIN_CALIBRAR' :
    metadata.incluye_ot === true ? '40 minutos más OT · SIN_CALIBRAR' : metadata.incluye_ot === false ? '40 minutos de regulación, sin OT · SIN_CALIBRAR' : 'Convención OT: N/D';
  return 'Regulación NBA de 48 minutos, sin OT · Confianza heurística no validada';
}
