/**
 * formateadores.ts — Funciones para formatear datos
 */

/**
 * Formatea un número como porcentaje
 */
export function formatearPorcentaje(valor: number, decimales = 1): string {
  return `${(valor * 100).toFixed(decimales)}%`;
}

/**
 * Formatea un número con signo
 */
export function formatearConSigno(valor: number, decimales = 2): string {
  const signo = valor >= 0 ? '+' : '';
  return `${signo}${valor.toFixed(decimales)}`;
}

/**
 * Formatea puntos con unidad
 */
export function formatearPuntos(valor: number, decimales = 1): string {
  return `${valor.toFixed(decimales)} pts`;
}

/**
 * Formatea una fecha ISO a formato legible
 */
export function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleString('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Capitaliza la primera letra
 */
export function capitalizar(texto: string): string {
  if (!texto) return '';
  return texto.charAt(0).toUpperCase() + texto.slice(1).toLowerCase();
}
