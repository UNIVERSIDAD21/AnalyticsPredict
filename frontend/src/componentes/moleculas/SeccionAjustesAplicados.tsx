/**
 * SeccionAjustesAplicados.tsx — Visualización de ajustes contextuales aplicados
 *
 * Tabla/lista que muestra cada ajuste individual aplicado con su valor
 * en puntos, dirección (sube/baja), y descripción.
 */

import { useState, useMemo } from 'react';
import {
  Zap,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Tarjeta } from '../atomos';
import type { AjusteIndividual } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

/** Valor máximo de referencia para la barra de progreso (en puntos) */
const MAX_PUNTOS_BARRA = 5;

/** Mapeo de factores a nombres legibles */
const NOMBRES_FACTORES: Record<string, string> = {
  back_to_back: 'Back-to-back',
  descanso_asimetrico: 'Ventaja de descanso',
  h2h_tendencia: 'Tendencia H2H',
  forma_ofensiva_equipo: 'Forma ofensiva (equipo)',
  forma_ofensiva_rival: 'Forma ofensiva (rival)',
  forma_defensiva_equipo: 'Forma defensiva (equipo)',
  forma_defensiva_rival: 'Forma defensiva (rival)',
  ritmo_juego: 'Ritmo de juego',
  lesiones: 'Lesiones clave',
  viaje: 'Fatiga por viaje',
};


// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSeccionAjustes {
  /** Lista de ajustes individuales aplicados */
  ajustes: AjusteIndividual[];
  /** Ajuste total (ya capped si aplica) */
  ajusteTotal: number;
  /** Indica si el ajuste fue limitado por el cap */
  fueCapped: boolean;
  /** Iniciar expandido o colapsado */
  inicialmenteExpandido?: boolean;
  /** Clase CSS adicional */
  className?: string;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

/**
 * Obtiene el nombre legible de un factor
 */
function obtenerNombreFactor(factor: string): string {
  return NOMBRES_FACTORES[factor] || factor.replace(/_/g, ' ');
}


/**
 * Calcula el porcentaje de la barra de progreso
 */
function calcularPorcentajeBarra(valor: number): number {
  const valorAbs = Math.abs(valor);
  return Math.min((valorAbs / MAX_PUNTOS_BARRA) * 100, 100);
}

/**
 * Formatea el valor del ajuste con signo
 */
function formatearValorAjuste(valor: number): string {
  const signo = valor >= 0 ? '+' : '';
  return `${signo}${valor.toFixed(1)} pts`;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE DE AJUSTE INDIVIDUAL
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaAjuste {
  ajuste: AjusteIndividual;
}

function TarjetaAjuste({ ajuste }: PropsTarjetaAjuste) {
  const esPositivo = ajuste.direccion === 'sube';
  const porcentajeBarra = calcularPorcentajeBarra(ajuste.valor);

  return (
    <div
      className={clsx(
        'p-3 rounded-lg border transition-colors',
        esPositivo
          ? 'bg-neon-verde/5 border-neon-verde/20 hover:border-neon-verde/30'
          : 'bg-neon-rojo/5 border-neon-rojo/20 hover:border-neon-rojo/30'
      )}
    >
      {/* Encabezado del ajuste */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          {/* Icono de dirección */}
          <span
            className={clsx(
              'flex-shrink-0',
              esPositivo ? 'text-neon-verde' : 'text-neon-rojo'
            )}
            aria-label={esPositivo ? 'Sube la predicción' : 'Baja la predicción'}
          >
            {esPositivo ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
          </span>

          {/* Nombre del factor */}
          <span className="text-sm font-medium text-texto-principal truncate">
            {obtenerNombreFactor(ajuste.factor)}
          </span>
        </div>

        {/* Valor del ajuste */}
        <span
          className={clsx(
            'text-sm font-mono font-semibold flex-shrink-0',
            esPositivo ? 'text-neon-verde' : 'text-neon-rojo'
          )}
        >
          {formatearValorAjuste(ajuste.valor)}
        </span>
      </div>

      {/* Descripción */}
      <p className="text-xs text-texto-secundario mb-3 leading-relaxed">
        {ajuste.descripcion}
      </p>

      {/* Barra de impacto */}
      <div className="h-1.5 bg-futurista-medio rounded-full overflow-hidden">
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-500',
            esPositivo
              ? 'bg-gradient-to-r from-neon-verde/60 to-neon-verde'
              : 'bg-gradient-to-r from-neon-rojo/60 to-neon-rojo'
          )}
          style={{ width: `${porcentajeBarra}%` }}
          role="progressbar"
          aria-valuenow={Math.abs(ajuste.valor)}
          aria-valuemin={0}
          aria-valuemax={MAX_PUNTOS_BARRA}
          aria-label={`Impacto: ${Math.abs(ajuste.valor).toFixed(1)} puntos`}
        />
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

export function SeccionAjustesAplicados({
  ajustes,
  ajusteTotal,
  fueCapped,
  inicialmenteExpandido = true,
  className,
}: PropsSeccionAjustes) {
  const [expandido, setExpandido] = useState(inicialmenteExpandido);

  // Ordenar ajustes por impacto absoluto (mayor primero)
  const ajustesOrdenados = useMemo(() => {
    return [...ajustes].sort((a, b) => Math.abs(b.valor) - Math.abs(a.valor));
  }, [ajustes]);

  // Determinar color del total
  const esPositivo = ajusteTotal >= 0;

  // Si no hay ajustes, no renderizar nada
  if (ajustes.length === 0) {
    return null;
  }

  return (
    <Tarjeta className={clsx('space-y-4', className)} padding="md">
      {/* Encabezado colapsable */}
      <button
        onClick={() => setExpandido(!expandido)}
        className="w-full flex items-center justify-between gap-2 group"
        aria-expanded={expandido}
        aria-controls="lista-ajustes"
      >
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-neon-cyan" />
          <h3 className="text-lg font-futurista text-texto-principal tracking-wide">
            Ajustes Aplicados
          </h3>
          <span className="text-sm text-texto-terciario">
            ({ajustes.length})
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={clsx(
              'text-sm font-mono font-semibold',
              esPositivo ? 'text-neon-verde' : 'text-neon-rojo'
            )}
          >
            {formatearValorAjuste(ajusteTotal)}
          </span>
          {expandido ? (
            <ChevronUp className="w-5 h-5 text-texto-terciario group-hover:text-texto-secundario transition-colors" />
          ) : (
            <ChevronDown className="w-5 h-5 text-texto-terciario group-hover:text-texto-secundario transition-colors" />
          )}
        </div>
      </button>

      {/* Contenido colapsable */}
      {expandido && (
        <div id="lista-ajustes" className="space-y-3">
          {/* Lista de ajustes */}
          {ajustesOrdenados.map((ajuste, index) => (
            <TarjetaAjuste key={`${ajuste.factor}-${index}`} ajuste={ajuste} />
          ))}

          {/* Separador */}
          <div className="h-px bg-gradient-to-r from-neon-cyan/10 via-neon-cyan/30 to-neon-cyan/10" />

          {/* Total */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-futurista-medio/50">
            <span className="text-sm font-semibold text-texto-principal uppercase tracking-wider">
              Ajuste Neto
            </span>
            <div className="flex items-center gap-2">
              <span
                className={clsx(
                  'text-lg font-mono font-bold',
                  esPositivo ? 'text-neon-verde' : 'text-neon-rojo'
                )}
              >
                {formatearValorAjuste(ajusteTotal)}
              </span>
              {fueCapped && (
                <span
                  className="text-xs text-advertencia-500 bg-advertencia-500/10 px-2 py-0.5 rounded"
                  title="El ajuste total fue limitado para evitar correcciones excesivas"
                >
                  (limitado)
                </span>
              )}
            </div>
          </div>

          {/* Nota informativa si fue capped */}
          {fueCapped && (
            <p className="text-xs text-texto-terciario italic">
              El ajuste total fue limitado por el sistema para mantener
              predicciones conservadoras.
            </p>
          )}
        </div>
      )}
    </Tarjeta>
  );
}
