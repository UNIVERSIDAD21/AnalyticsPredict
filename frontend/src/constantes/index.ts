/**
 * index.ts — Constantes de la aplicación
 */

/**
 * Mercados disponibles
 */
export const MERCADOS = ['Q1', 'Q2', 'Q3', 'Q4', 'COMPLETO'] as const;

/**
 * Niveles de confianza
 */
export const NIVELES_CONFIANZA = ['ALTA', 'MEDIA', 'BAJA'] as const;

/**
 * Tipos de recomendación
 */
export const TIPOS_RECOMENDACION = ['VALOR', 'JUSTO', 'EVITAR'] as const;

/**
 * Mensajes de error comunes
 */
export const MENSAJES_ERROR = {
  CONEXION: 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo.',
  EQUIPO_NO_ENCONTRADO: 'El equipo seleccionado no se encontró en el sistema.',
  LINEA_INVALIDA: 'La línea ingresada no es válida.',
  CUOTA_INVALIDA: 'La cuota debe ser mayor a 1.00.',
  MISMO_EQUIPO: 'El equipo local y visitante no pueden ser el mismo.',
  ERROR_GENERICO: 'Ocurrió un error inesperado. Intenta de nuevo.',
} as const;

/**
 * Colores por recomendación
 */
export const COLORES_RECOMENDACION = {
  VALOR: {
    fondo: 'bg-exito-50',
    texto: 'text-exito-600',
    borde: 'border-exito-500',
  },
  JUSTO: {
    fondo: 'bg-advertencia-50',
    texto: 'text-advertencia-600',
    borde: 'border-advertencia-500',
  },
  EVITAR: {
    fondo: 'bg-error-50',
    texto: 'text-error-600',
    borde: 'border-error-500',
  },
} as const;
