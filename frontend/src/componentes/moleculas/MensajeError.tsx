/**
 * MensajeError.tsx — Componente para mostrar errores con estilo futurista
 */

import { AlertCircle, X } from 'lucide-react';

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
 * Mensaje de error con estilo futurista
 */
export function MensajeError({
  mensaje,
  onCerrar,
  titulo = 'Error',
}: PropsMensajeError) {
  return (
    <div
      className="rounded-xl p-4 animate-entrada border border-neon-rojo/30 bg-neon-rojo/10"
      role="alert"
    >
      <div className="flex items-start gap-3">
        {/* Icono */}
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-neon-rojo/20 flex items-center justify-center">
          <AlertCircle className="text-neon-rojo" size={18} />
        </div>

        {/* Contenido */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-neon-rojo">
            {titulo}
          </h3>
          <p className="text-sm text-texto-secundario mt-1">
            {mensaje}
          </p>
        </div>

        {/* Botón cerrar */}
        {onCerrar && (
          <button
            onClick={onCerrar}
            className="text-neon-rojo/70 hover:text-neon-rojo transition-colors p-1 rounded hover:bg-neon-rojo/10"
            aria-label="Cerrar mensaje"
          >
            <X size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
