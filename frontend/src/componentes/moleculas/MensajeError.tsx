/**
 * MensajeError.tsx — Componente para mostrar errores
 */

import { AlertCircle, X } from 'lucide-react';
import { Tarjeta } from '../atomos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsMensajeError {
  /** Mensaje de error a mostrar */
  mensaje: string;
  /** Callback para cerrar el mensaje */
  onCerrar?: () => void;
  /** Título del error */
  titulo?: string;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Mensaje de error con estilo de alerta
 */
export function MensajeError({
  mensaje,
  onCerrar,
  titulo = 'Error',
}: PropsMensajeError) {
  return (
    <Tarjeta
      variante="borde"
      padding="md"
      className="border-error-500 bg-error-50 animate-entrada"
      role="alert"
    >
      <div className="flex items-start gap-3">
        {/* Icono */}
        <AlertCircle className="text-error-500 flex-shrink-0 mt-0.5" size={20} />

        {/* Contenido */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-error-600">
            {titulo}
          </h3>
          <p className="text-sm text-error-600 mt-1">
            {mensaje}
          </p>
        </div>

        {/* Botón cerrar */}
        {onCerrar && (
          <button
            onClick={onCerrar}
            className="text-error-500 hover:text-error-600 transition-colors"
            aria-label="Cerrar mensaje"
          >
            <X size={18} />
          </button>
        )}
      </div>
    </Tarjeta>
  );
}
