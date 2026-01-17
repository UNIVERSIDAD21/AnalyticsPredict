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
    mensaje:
      'Las cuotas suman menos de 100%. Esto suele indicar un error en los datos o una posible oportunidad de arbitraje; conviene revisar antes de apostar.',
    categoria: 'error',
  },
  'OVERROUND_ALTO_REVISAR': {
    mensaje:
      'Las cuotas suman más de 110%, lo que significa un margen muy alto para la casa. La apuesta puede estar inflada o poco conveniente.',
    categoria: 'warning',
  },
  'DEVIG_ESTRICTO_REQUIERE_AMBAS_CUOTAS': {
    mensaje:
      'Para calcular la probabilidad justa con precisión necesitamos la cuota del over y del under. Si falta una, el cálculo no es exacto.',
    categoria: 'warning',
  },
  'DEVIG_ESTIMADO_PENALIZA': {
    mensaje:
      'No se pudo quitar el margen de la casa con datos exactos, así que se usa una estimación. Por seguridad se reduce la confianza y el tamaño de la apuesta.',
    categoria: 'info',
  },
  'De-vig estimado: stake penalizado': {
    mensaje:
      'Se estimó el margen de la casa porque faltan datos exactos. Por eso el monto sugerido se reduce para ser más conservador.',
    categoria: 'info',
  },
  'Sin devig: stake penalizado': {
    mensaje:
      'No se pudo calcular la probabilidad justa (sin de-vig). Por seguridad, el monto sugerido se reduce mucho.',
    categoria: 'warning',
  },

  // Sizing
  'Kelly <= 0: no apostar': {
    mensaje:
      'Con la cuota y la probabilidad actuales, la fórmula indica que no hay valor. Lo más prudente es no apostar.',
    categoria: 'error',
  },
  'Cap diario aplicado': {
    mensaje:
      'Se aplicó un tope diario. Aunque el cálculo sugería más, el sistema limita el porcentaje máximo que se puede arriesgar en el día.',
    categoria: 'info',
  },
  'Cap por apuesta aplicado': {
    mensaje:
      'Se aplicó un tope por apuesta. El monto sugerido se bajó al máximo permitido para una sola jugada.',
    categoria: 'info',
  },
  'Stake por debajo del mínimo': {
    mensaje:
      'El monto calculado es menor que el mínimo permitido. Puede que no se pueda apostar con ese valor.',
    categoria: 'warning',
  },
  'Sin bankroll disponible para sizing': {
    mensaje:
      'No se ingresó un bankroll (fondo disponible), por eso no se puede calcular el monto exacto a apostar.',
    categoria: 'warning',
  },

  // Score/Riesgo
  'RIESGO_ALTO': {
    mensaje:
      'El modelo detecta mucha variación en los resultados (desviación alta). Eso hace que la predicción sea menos estable y más riesgosa.',
    categoria: 'warning',
  },
  'Riesgo alto: desviación alta': {
    mensaje:
      'La desviación es alta, lo que significa que los resultados pueden variar mucho. Por eso se considera una apuesta más riesgosa.',
    categoria: 'warning',
  },
  'SIN_DEVIG': {
    mensaje:
      'No se pudo quitar el margen de la casa (de-vig), así que no contamos con la probabilidad justa exacta.',
    categoria: 'warning',
  },

  // Contexto/ajustes
  'Ambos equipos en BACK-TO-BACK': {
    mensaje:
      'Ambos equipos juegan en días seguidos. Esto suele generar cansancio y puede bajar el ritmo y los puntos.',
    categoria: 'warning',
  },
  'Back-to-back confirmado en uno de los equipos': {
    mensaje:
      'Uno de los equipos juega en días seguidos, lo que puede afectar su energía y rendimiento.',
    categoria: 'warning',
  },
  'Ventaja significativa de descanso': {
    mensaje:
      'Un equipo tuvo más días de descanso que el otro. Esa ventaja puede influir en el resultado.',
    categoria: 'info',
  },
  'Diferencia H2H vs base mayor a 10 pts': {
    mensaje:
      'En los enfrentamientos directos recientes, el promedio de puntos se aleja más de 10 puntos del promedio base. Es una señal de historial atípico.',
    categoria: 'warning',
  },
  'Ajuste individual capped por límite máximo': {
    mensaje:
      'Un ajuste era demasiado grande y se recortó al límite permitido para evitar exageraciones.',
    categoria: 'info',
  },
  'Ajuste total capped por límite global': {
    mensaje:
      'La suma de ajustes superaba el máximo permitido, así que se recortó al límite global.',
    categoria: 'info',
  },
  'Múltiples ajustes significativos (>6 pts)': {
    mensaje:
      'Se aplicaron varios ajustes grandes (más de 6 puntos en total), lo que indica cambios importantes en el contexto.',
    categoria: 'warning',
  },
  'Predicción alejada del histórico H2H': {
    mensaje:
      'La predicción actual está lejos de lo que suele pasar en los enfrentamientos directos entre estos equipos. Conviene revisar.',
    categoria: 'warning',
  },
};

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function normalizarCodigo(codigo: string) {
  return codigo.replace(/^⚠️\s*/u, '').trim().replace(/\.+$/u, '').trim();
}

function procesarAdvertencia(codigo: string): AdvertenciaProcesada {
  const codigoNormalizado = normalizarCodigo(codigo);
  const mapeo = MAPEO_ADVERTENCIAS[codigoNormalizado];

  if (mapeo) {
    return {
      codigo,
      mensaje: mapeo.mensaje,
      categoria: mapeo.categoria,
    };
  }

  if (codigoNormalizado.startsWith('config_sizing')) {
    return {
      codigo,
      mensaje:
        'La configuración de límites de apuesta tiene un dato faltante o inválido, así que se usaron valores por defecto.',
      categoria: 'warning',
    };
  }

  // Código desconocido: mostrar como info con el código
  return {
    codigo,
    mensaje: codigoNormalizado.replace(/_/g, ' ').toLowerCase(),
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
