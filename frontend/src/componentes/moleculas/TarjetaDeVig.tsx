/**
 * TarjetaDeVig.tsx — Muestra el proceso de de-vig de forma profesional
 *
 * Soporta 3 variantes:
 * - exacto: ambas cuotas ingresadas, overround real
 * - estimado: falta cuota opuesta, vig estimado
 * - no_aplicado: sin información suficiente para de-vig
 */

import { CheckCircle, AlertTriangle, XCircle, TrendingUp, Percent, HelpCircle } from 'lucide-react';
import { Tarjeta } from '../atomos';
import { MetodoDeVig } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaDeVig {
  /** Método de de-vig utilizado */
  metodo: MetodoDeVig;

  /** Overround calculado (puede ser null) */
  overround: number | null;

  /** Probabilidad cruda del mercado (1/cuota) */
  pMktRaw: number;

  /** Probabilidad justa después de eliminar vig */
  pMktFair: number;

  /** Edge crudo (antes de calibración) */
  edgeRaw: number | null;

  /** Edge real (después de calibración) - EL QUE IMPORTA */
  edgeReal: number | null;

  /** Advertencias de de-vig */
  advertencias?: string[];
}

// ══════════════════════════════════════════════════════════════
// CONFIGURACIÓN VISUAL POR MÉTODO
// ══════════════════════════════════════════════════════════════

function obtenerConfigMetodo(metodo: MetodoDeVig) {
  switch (metodo) {
    case 'exacto':
      return {
        icono: CheckCircle,
        titulo: 'DE-VIG EXACTO',
        descripcion: 'Ambas cuotas disponibles, cálculo preciso del overround',
        colorFondo: 'bg-neon-verde/10',
        colorBorde: 'border-neon-verde/30',
        colorTexto: 'text-neon-verde',
        colorIcono: 'text-neon-verde',
      };
    case 'estimado':
      return {
        icono: AlertTriangle,
        titulo: 'DE-VIG ESTIMADO',
        descripcion: 'Solo una cuota disponible, se usa vig estimado (4.5%)',
        colorFondo: 'bg-neon-amarillo/10',
        colorBorde: 'border-neon-amarillo/30',
        colorTexto: 'text-neon-amarillo',
        colorIcono: 'text-neon-amarillo',
      };
    case 'no_aplicado':
    default:
      return {
        icono: XCircle,
        titulo: 'SIN DE-VIG',
        descripcion: 'No hay información suficiente para calcular probabilidad justa',
        colorFondo: 'bg-neon-rojo/10',
        colorBorde: 'border-neon-rojo/30',
        colorTexto: 'text-neon-rojo',
        colorIcono: 'text-neon-rojo',
      };
  }
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

function formatearPorcentaje(valor: number | null | undefined, decimales = 2): string {
  if (valor === null || valor === undefined || !isFinite(valor)) {
    return '—';
  }
  const porcentaje = valor * 100;
  const signo = porcentaje >= 0 ? '+' : '';
  return `${signo}${porcentaje.toFixed(decimales)}%`;
}

function formatearOverround(overround: number | null): string {
  if (overround === null || !isFinite(overround)) {
    return '—';
  }
  return overround.toFixed(4);
}

function calcularVig(overround: number | null): string {
  if (overround === null || !isFinite(overround)) {
    return '—';
  }
  const vig = (overround - 1) * 100;
  if (!isFinite(vig)) return '—';
  return `${vig.toFixed(2)}%`;
}

function formatearProbabilidad(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || !isFinite(valor) || valor < 0 || valor > 1) {
    return '—';
  }
  return `${(valor * 100).toFixed(1)}%`;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra el proceso de de-vig de forma profesional.
 * Incluye método, overround, probabilidades y comparación de edges.
 */
export function TarjetaDeVig({
  metodo,
  overround,
  pMktRaw,
  pMktFair,
  edgeRaw,
  edgeReal,
  advertencias = [],
}: PropsTarjetaDeVig) {
  const config = obtenerConfigMetodo(metodo);
  const Icono = config.icono;
  const overroundSano = overround !== null && isFinite(overround) && overround > 0.9 && overround < 2.0;

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Encabezado con método */}
      <div className={`-m-6 mb-5 p-4 rounded-t-xl ${config.colorFondo} ${config.colorBorde} border-b`}>
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${config.colorFondo} flex items-center justify-center flex-shrink-0 border ${config.colorBorde}`}>
            <Icono className={`w-5 h-5 ${config.colorIcono}`} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className={`text-sm font-futurista font-bold tracking-wider ${config.colorTexto}`}>
              {config.titulo}
            </h3>
            <p className="text-xs text-texto-secundario mt-0.5">
              {config.descripcion}
            </p>
          </div>
        </div>
      </div>

      {/* Métricas principales */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {/* Overround */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <Percent size={12} />
            <span className="text-[10px] uppercase tracking-wider">Overround</span>
          </div>
          <div className="text-lg font-mono font-bold text-neon-cyan">
            {formatearOverround(overroundSano ? overround : null)}
          </div>
          <div className="text-[10px] text-texto-terciario mt-1">
            Vig: {calcularVig(overroundSano ? overround : null)}
          </div>
        </div>

        {/* Prob. Cruda */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <span className="text-[10px] uppercase tracking-wider">P. Implícita</span>
          </div>
          <div className="text-lg font-mono font-bold text-texto-principal">
            {formatearProbabilidad(pMktRaw)}
          </div>
          <div className="text-[10px] text-texto-terciario mt-1">
            Cruda (1/cuota)
          </div>
        </div>

        {/* Prob. Justa */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <span className="text-[10px] uppercase tracking-wider">P. Justa</span>
          </div>
          <div className={`text-lg font-mono font-bold ${metodo === 'exacto' ? 'text-neon-verde' : 'text-texto-principal'}`}>
            {formatearProbabilidad(pMktFair)}
          </div>
          <div className="text-[10px] text-texto-terciario mt-1">
            Sin vig
          </div>
        </div>

        {/* Diferencia */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <span className="text-[10px] uppercase tracking-wider">Diferencia</span>
          </div>
          <div className="text-lg font-mono font-bold text-neon-magenta">
            {isFinite(pMktRaw) && isFinite(pMktFair) ? `${((pMktRaw - pMktFair) * 100).toFixed(2)} pp` : '—'}
          </div>
          <div className="text-[10px] text-texto-terciario mt-1">
            Vig aplicado
          </div>
        </div>
      </div>

      {/* Comparación de Edges - LA PARTE MÁS IMPORTANTE */}
      <div className="p-4 rounded-lg bg-gradient-to-r from-futurista-oscuro/50 to-futurista-oscuro/30 border border-neon-cyan/10">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp size={16} className="text-neon-cyan" />
          <span className="text-xs font-bold uppercase tracking-wider text-neon-cyan">
            Comparación de Edges
          </span>
          <div className="group relative ml-auto">
            <HelpCircle size={14} className="text-texto-terciario cursor-help" />
            <div className="absolute bottom-full right-0 mb-2 w-64 p-3 rounded-lg bg-futurista-oscuro border border-neon-cyan/20 text-xs text-texto-secundario opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
              <strong className="text-neon-cyan">Edge</strong> = Tu ventaja sobre la casa.
              <br /><br />
              <strong>Edge Raw:</strong> Antes de calibrar probabilidades.
              <br />
              <strong>Edge Real:</strong> Después de calibración, ajustado por vig justo. <span className="text-neon-verde">Este es el que importa.</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Edge Raw */}
          <div className="text-center">
            <div className="text-[10px] uppercase tracking-wider text-texto-terciario mb-1">
              Edge Raw
            </div>
            <div className={`text-2xl font-mono font-bold ${
              edgeRaw !== null && edgeRaw >= 0
                ? 'text-neon-verde/70'
                : 'text-neon-rojo/70'
            }`}>
              {formatearPorcentaje(edgeRaw)}
            </div>
            <div className="text-[10px] text-texto-terciario mt-1">
              Sin calibrar
            </div>
          </div>

          {/* Edge Real - DESTACADO */}
          <div className="text-center relative">
            {/* Indicador visual de que este es el importante */}
            <div className="absolute -top-1 -right-1 px-2 py-0.5 rounded-full bg-neon-verde/20 border border-neon-verde/40">
              <span className="text-[8px] font-bold uppercase tracking-wider text-neon-verde">
                USAR ESTE
              </span>
            </div>
            <div className="text-[10px] uppercase tracking-wider text-texto-terciario mb-1">
              Edge Real
            </div>
            <div className={`text-2xl font-mono font-bold ${
              edgeReal !== null && edgeReal >= 0
                ? 'text-neon-verde texto-glow-verde'
                : 'text-neon-rojo texto-glow-rojo'
            }`}>
              {formatearPorcentaje(edgeReal)}
            </div>
            <div className="text-[10px] text-texto-terciario mt-1">
              Calibrado + de-vig
            </div>
          </div>
        </div>
      </div>

      {advertencias.length > 0 && (
        <div className="mt-4 p-3 rounded-lg bg-neon-amarillo/5 border border-neon-amarillo/20">
          <div className="flex items-center gap-2 mb-2 text-neon-amarillo text-xs font-bold uppercase tracking-wider">
            <AlertTriangle size={12} /> Advertencias de de-vig
          </div>
          <ul className="space-y-1 text-[10px] text-texto-secundario">
            {advertencias.map((a, i) => <li key={i}>• {a}</li>)}
          </ul>
        </div>
      )}

      {/* Nota explicativa sobre de-vig */}
      <div className="mt-4 pt-3 border-t border-neon-cyan/10">
        <div className="flex items-start gap-2">
          <HelpCircle size={12} className="text-texto-terciario mt-0.5 flex-shrink-0" />
          <p className="text-[10px] text-texto-terciario leading-relaxed">
            <strong className="text-neon-cyan">De-vig</strong> elimina el margen de la casa de las cuotas
            para obtener la probabilidad justa del mercado. El <strong className="text-neon-verde">Edge Real</strong> es
            tu ventaja real después de ajustar por calibración y vig.
          </p>
        </div>
      </div>
    </Tarjeta>
  );
}
