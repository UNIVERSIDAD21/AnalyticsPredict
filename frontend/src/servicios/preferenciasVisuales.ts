export interface PreferenciasVisualesLocal {
  tema: 'oscuro' | 'claro'; densidad: 'comoda' | 'compacta'; texto: 'normal' | 'grande';
}
export const CLAVE_VISUAL = 'analyticspredict-visual-v1';
const PREDETERMINADAS: PreferenciasVisualesLocal = { tema: 'oscuro', densidad: 'comoda', texto: 'normal' };
export function validarPreferencias(valor: unknown): PreferenciasVisualesLocal {
  if (!valor || typeof valor !== 'object' || !('tema' in valor) || !('densidad' in valor) || !('texto' in valor) ||
    !['oscuro', 'claro'].includes(String(valor.tema)) || !['comoda', 'compacta'].includes(String(valor.densidad)) || !['normal', 'grande'].includes(String(valor.texto))) {
    throw new Error('La apariencia del respaldo no tiene un formato compatible.');
  }
  return { tema: valor.tema, densidad: valor.densidad, texto: valor.texto } as PreferenciasVisualesLocal;
}
export function leerAparienciaGuardada(): PreferenciasVisualesLocal | null {
  const raw = localStorage.getItem(CLAVE_VISUAL);
  return raw === null ? null : validarPreferencias(JSON.parse(raw));
}
export function leerPreferencias(): PreferenciasVisualesLocal {
  try { return leerAparienciaGuardada() ?? { ...PREDETERMINADAS }; }
  catch { return { ...PREDETERMINADAS }; }
}
export function aplicarPreferencias(preferencias: PreferenciasVisualesLocal) {
  Object.assign(document.documentElement.dataset, preferencias);
}
