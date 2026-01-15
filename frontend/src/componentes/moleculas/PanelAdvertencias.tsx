/**
 * PanelAdvertencias.tsx — Muestra advertencias del backend categorizadas
 *
 * Categoriza las advertencias en:
 * - error: Problemas serios que requieren atención inmediata
 * - warning: Precauciones importantes
 * - info: Información contextual
 *
 * Incluye mapeo de códigos a mensajes humanos legibles.
 */

import { useState } from 'react';
import { AlertTriangle, AlertOctagon, Info, ChevronDown, ChevronUp } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsPanelAdvertencias {
  /** Lista de advertencias del backend */
  advertencias: string[];
}

type CategoriaAdvertencia = 'error' | 'warning' | 'info';

interface AdvertenciaProcesada {
  codigo: string;
  mensaje: string;
  categoria: CategoriaAdvertencia;
}

// ══════════════════════════════════════════════════════════════
// MAPEO DE CÓDIGOS A MENSAJES Y CATEGORÍAS
// ══════════════════════════════════════════════════════════════

const MAPEO_ADVERTENCIAS: Record<string, { mensaje: string; categoria: CategoriaAdvertencia }> = {
  // De-Vig
  'OVERROUND_BAJO_POSIBLE_ARB': {
    mensaje: 'Overround menor a 100%: posible arbitraje o error en cuotas',
    categoria: 'error',
  },
  'OVERROUND_ALTO_REVISAR': {
    mensaje: 'Overround superior al 10%: margen de la casa alto, revisar cuotas',
    categoria: 'warning',
  },
  'DEVIG_ESTRICTO_REQUIERE_AMBAS_CUOTAS': {
    mensaje: 'El modo estricto requiere ambas cuotas para de-vig exacto',
    categoria: 'warning',
  },
  'DEVIG_ESTIMADO_PENALIZA': {
    mensaje: 'De-vig estimado: se aplica penalización por vig desconocido',
    categoria: 'info',
  },

  // Sizing
  'Kelly <= 0: no apostar': {
    mensaje: 'Kelly negativo o cero: no se recomienda apostar',
    categoria: 'error',
  },
  'Cap por apuesta aplicado': {
    mensaje: 'Se aplicó límite máximo por apuesta',
    categoria: 'info',
  },
  'Stake por debajo del mínimo': {
    mensaje: 'El stake calculado está por debajo del mínimo permitido',
    categoria: 'warning',
  },
  'Sin bankroll disponible para sizing': {
    mensaje: 'No hay bankroll configurado: no se puede calcular stake',
    categoria: 'warning',
  },

  // Score/Riesgo
  'RIESGO_ALTO': {
    mensaje: 'Alta volatilidad detectada en este mercado',
    categoria: 'warning',
  },
  'SIN_DEVIG': {
    mensaje: 'No se pudo aplicar de-vig: probabilidad justa no disponible',
    categoria: 'warning',
  },
};

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function procesarAdvertencia(codigo: string): AdvertenciaProcesada {
  const mapeo = MAPEO_ADVERTENCIAS[codigo];

  if (mapeo) {
    return {
      codigo,
      mensaje: mapeo.mensaje,
      categoria: mapeo.categoria,
    };
  }

  // Código desconocido: mostrar como info con el código
  return {
    codigo,
    mensaje: codigo.replace(/_/g, ' ').toLowerCase(),
    categoria: 'info',
  };
}

function obtenerConfigCategoria(categoria: CategoriaAdvertencia) {
  switch (categoria) {
    case 'error':
      return {
        icono: AlertOctagon,
        bgColor: 'bg-neon-rojo/10',
        borderColor: 'border-neon-rojo/30',
        textColor: 'text-neon-rojo',
        iconColor: 'text-neon-rojo',
      };
    case 'warning':
      return {
        icono: AlertTriangle,
        bgColor: 'bg-neon-amarillo/10',
        borderColor: 'border-neon-amarillo/30',
        textColor: 'text-neon-amarillo',
        iconColor: 'text-neon-amarillo',
      };
    case 'info':
      return {
        icono: Info,
        bgColor: 'bg-neon-cyan/10',
        borderColor: 'border-neon-cyan/30',
        textColor: 'text-neon-cyan',
        iconColor: 'text-neon-cyan',
      };
  }
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Panel que muestra advertencias del backend categorizadas.
 * Solo se renderiza si hay advertencias.
 */
export function PanelAdvertencias({ advertencias }: PropsPanelAdvertencias) {
  const [expandido, setExpandido] = useState(true);

  // No mostrar si no hay advertencias
  if (!advertencias || advertencias.length === 0) {
    return null;
  }

  // Procesar y ordenar advertencias (errores primero, luego warnings, luego info)
  const advertenciasProcesadas = advertencias
    .map(procesarAdvertencia)
    .sort((a, b) => {
      const orden: Record<CategoriaAdvertencia, number> = { error: 0, warning: 1, info: 2 };
      return orden[a.categoria] - orden[b.categoria];
    });

  const tieneErrores = advertenciasProcesadas.some(a => a.categoria === 'error');
  const tieneWarnings = advertenciasProcesadas.some(a => a.categoria === 'warning');
  const muchasAdvertencias = advertencias.length > 3;

  // Determinar color del header según la advertencia más grave
  const colorHeader = tieneErrores
    ? 'bg-neon-rojo/10 border-neon-rojo/30'
    : tieneWarnings
      ? 'bg-neon-amarillo/10 border-neon-amarillo/30'
      : 'bg-neon-cyan/10 border-neon-cyan/30';

  const textoHeader = tieneErrores
    ? 'text-neon-rojo'
    : tieneWarnings
      ? 'text-neon-amarillo'
      : 'text-neon-cyan';

  return (
    <div className={`rounded-xl overflow-hidden border ${tieneErrores ? 'border-neon-rojo/30' : tieneWarnings ? 'border-neon-amarillo/30' : 'border-neon-cyan/30'} animate-deslizar-arriba`}>
      {/* Header */}
      <button
        className={`w-full p-3 ${colorHeader} flex items-center justify-between transition-colors hover:opacity-90`}
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-2">
          {tieneErrores ? (
            <AlertOctagon size={18} className="text-neon-rojo" />
          ) : tieneWarnings ? (
            <AlertTriangle size={18} className="text-neon-amarillo" />
          ) : (
            <Info size={18} className="text-neon-cyan" />
          )}
          <span className={`text-sm font-bold uppercase tracking-wider ${textoHeader}`}>
            {advertencias.length} {advertencias.length === 1 ? 'Advertencia' : 'Advertencias'}
          </span>
        </div>
        {muchasAdvertencias && (
          expandido ? (
            <ChevronUp size={18} className={textoHeader} />
          ) : (
            <ChevronDown size={18} className={textoHeader} />
          )
        )}
      </button>

      {/* Lista de advertencias */}
      {expandido && (
        <div className="p-3 space-y-2 bg-futurista-oscuro/30">
          {advertenciasProcesadas.map((adv, idx) => {
            const config = obtenerConfigCategoria(adv.categoria);
            const Icono = config.icono;

            return (
              <div
                key={idx}
                className={`p-3 rounded-lg ${config.bgColor} ${config.borderColor} border flex items-start gap-3`}
              >
                <Icono size={16} className={`${config.iconColor} flex-shrink-0 mt-0.5`} />
                <div className="flex-1 min-w-0">
                  <p className={`text-sm ${config.textColor}`}>
                    {adv.mensaje}
                  </p>
                  {/* Mostrar código si es diferente al mensaje */}
                  {adv.codigo !== adv.mensaje && (
                    <p className="text-[10px] font-mono text-texto-terciario mt-1">
                      {adv.codigo}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
