/**
 * SelectorDeporte.tsx — Toggle para cambiar entre NBA y Fútbol
 */

import { useDeporte, type Deporte } from '../../contextos/DeporteContext';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface SelectorDeporteProps {
  /** Clase CSS adicional */
  className?: string;
  /** Tamaño del selector */
  tamaño?: 'sm' | 'md' | 'lg';
  /** Callback opcional al cambiar deporte */
  onChangeDeporte?: (deporte: Deporte) => void;
}

// ══════════════════════════════════════════════════════════════
// CONFIGURACIÓN
// ══════════════════════════════════════════════════════════════

interface ConfiguracionDeporte {
  icono: string;
  etiqueta: string;
  color: string;
}

const CONFIGURACION_DEPORTES: Record<Deporte, ConfiguracionDeporte> = {
  NBA: {
    icono: '🏀',
    etiqueta: 'BALONCESTO',
    color: 'neon-cyan',
  },
  WNBA: { icono: '🏀', etiqueta: 'WNBA', color: 'neon-cyan' },
  EUROLIGA: { icono: '🏀', etiqueta: 'EUROLIGA', color: 'neon-cyan' },
  FUTBOL: {
    icono: '⚽',
    etiqueta: 'FÚTBOL',
    color: 'neon-verde',
  },
};

const TAMAÑOS = {
  sm: {
    contenedor: 'p-0.5',
    boton: 'px-2 py-1 text-xs gap-1',
    icono: 'text-sm',
  },
  md: {
    contenedor: 'p-1',
    boton: 'px-3 py-1.5 text-xs gap-1.5',
    icono: 'text-base',
  },
  lg: {
    contenedor: 'p-1',
    boton: 'px-4 py-2 text-sm gap-2',
    icono: 'text-lg',
  },
};

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Selector visual para cambiar entre NBA y Fútbol
 */
export function SelectorDeporte({
  className = '',
  tamaño = 'md',
  onChangeDeporte,
}: SelectorDeporteProps) {
  const { deporteActivo, cambiarDeporte } = useDeporte();
  const estilosTamaño = TAMAÑOS[tamaño];

  return (
    <div
      className={`
        inline-flex rounded-full bg-futurista-oscuro/50
        border border-neon-cyan/20
        ${estilosTamaño.contenedor}
        ${className}
      `}
    >
      {(['NBA', 'FUTBOL'] as Deporte[]).map((grupo) => {
        const deporte = grupo === 'NBA' && deporteActivo !== 'FUTBOL' ? deporteActivo : grupo;
        const config = CONFIGURACION_DEPORTES[grupo];
        const esActivo = grupo === 'NBA' ? deporteActivo !== 'FUTBOL' : deporteActivo === 'FUTBOL';

        return (
          <button
            key={deporte}
            type="button"
            onClick={() => {
              cambiarDeporte(deporte, !onChangeDeporte);
              onChangeDeporte?.(deporte);
            }}
            className={`
              flex items-center rounded-full font-semibold uppercase tracking-wider
              transition-all duration-300 ease-out
              ${estilosTamaño.boton}
              ${
                esActivo
                  ? `
                    bg-${config.color}/20
                    border border-${config.color}/50
                    text-${config.color}
                    shadow-[0_0_15px_rgba(0,245,255,0.3)]
                  `
                  : `
                    text-texto-secundario
                    hover:text-texto-principal
                    hover:bg-futurista-medio/50
                    border border-transparent
                  `
              }
            `}
            aria-pressed={esActivo}
            aria-label={`Cambiar a ${config.etiqueta}`}
          >
            <span className={estilosTamaño.icono}>{config.icono}</span>
            <span>{config.etiqueta}</span>
          </button>
        );
      })}
    </div>
  );
}

/**
 * Versión compacta solo con iconos
 */
export function SelectorDeporteCompacto({ className = '' }: { className?: string }) {
  const { deporteActivo, cambiarDeporte } = useDeporte();

  return (
    <div
      className={`
        inline-flex rounded-lg bg-futurista-oscuro/50
        border border-neon-cyan/20 p-0.5
        ${className}
      `}
    >
      {(['NBA', 'FUTBOL'] as Deporte[]).map((grupo) => {
        const deporte = grupo === 'NBA' && deporteActivo !== 'FUTBOL' ? deporteActivo : grupo;
        const config = CONFIGURACION_DEPORTES[grupo];
        const esActivo = grupo === 'NBA' ? deporteActivo !== 'FUTBOL' : deporteActivo === 'FUTBOL';

        return (
          <button
            key={deporte}
            type="button"
            onClick={() => cambiarDeporte(deporte)}
            className={`
              w-8 h-8 flex items-center justify-center rounded-md
              text-lg transition-all duration-300 ease-out
              ${
                esActivo
                  ? `
                    bg-${config.color}/20
                    shadow-[0_0_10px_rgba(0,245,255,0.3)]
                  `
                  : `
                    hover:bg-futurista-medio/50
                    opacity-50 hover:opacity-100
                  `
              }
            `}
            aria-pressed={esActivo}
            aria-label={`Cambiar a ${config.etiqueta}`}
            title={config.etiqueta}
          >
            {config.icono}
          </button>
        );
      })}
    </div>
  );
}
