/**
 * validadores.ts — Funciones de validación
 */

/**
 * Verifica si un valor es un número válido
 */
export function esNumeroValido(valor: string | number): boolean {
  const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
  return !isNaN(numero) && isFinite(numero);
}

/**
 * Verifica si una línea es válida
 */
export function esLineaValida(valor: string | number): boolean {
  if (!esNumeroValido(valor)) return false;
  const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
  return numero > 0 && numero <= 400;
}

/**
 * Verifica si una cuota es válida
 */
export function esCuotaValida(valor: string | number): boolean {
  if (!esNumeroValido(valor)) return false;
  const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
  return numero > 1 && numero <= 100;
}

/**
 * Verifica si un string no está vacío
 */
export function noEstaVacio(valor: string | null | undefined): boolean {
  return Boolean(valor?.trim());
}
