/**
 * Toast.tsx — Notificación flotante con estilo futurista
 */

import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

export type TipoToast = 'success' | 'info' | 'warning' | 'error';

interface PropsToast {
  titulo: string;
  mensaje: string;
  tipo?: TipoToast;
  onCerrar?: () => void;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

function obtenerConfigToast(tipo: TipoToast) {
  switch (tipo) {
    case 'success':
      return {
        icono: CheckCircle2,
        borde: 'border-neon-verde/40',
        fondo: 'bg-neon-verde/10',
        texto: 'text-neon-verde',
      };
    case 'warning':
      return {
        icono: AlertTriangle,
        borde: 'border-neon-amarillo/40',
        fondo: 'bg-neon-amarillo/10',
        texto: 'text-neon-amarillo',
      };
    case 'error':
      return {
        icono: XCircle,
        borde: 'border-neon-rojo/40',
        fondo: 'bg-neon-rojo/10',
        texto: 'text-neon-rojo',
      };
    case 'info':
    default:
      return {
        icono: Info,
        borde: 'border-neon-cyan/40',
        fondo: 'bg-neon-cyan/10',
        texto: 'text-neon-cyan',
      };
  }
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

export function Toast({
  titulo,
  mensaje,
  tipo = 'info',
  onCerrar,
}: PropsToast) {
  const config = obtenerConfigToast(tipo);
  const Icono = config.icono;

  return (
    <div className={`w-full max-w-sm rounded-xl border ${config.borde} ${config.fondo} p-4 shadow-lg backdrop-blur animate-entrada`}>
      <div className="flex items-start gap-3">
        <div className={`w-9 h-9 rounded-lg ${config.fondo} flex items-center justify-center border ${config.borde}`}>
          <Icono size={18} className={config.texto} />
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-semibold ${config.texto}`}>
            {titulo}
          </p>
          <p className="text-sm text-texto-secundario mt-1">
            {mensaje}
          </p>
        </div>
        {onCerrar && (
          <button
            type="button"
            onClick={onCerrar}
            className="text-texto-terciario hover:text-texto-principal transition-colors"
            aria-label="Cerrar notificación"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
