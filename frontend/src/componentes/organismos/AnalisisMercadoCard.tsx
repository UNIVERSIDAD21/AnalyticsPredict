/**
 * AnalisisMercadoCard.tsx — Análisis de valor con estilo futurista
 */

import { CheckCircle, XCircle, MinusCircle, TrendingUp, Percent, Calculator } from 'lucide-react';
import { Tarjeta } from '../atomos';
import { AnalisisMercado, TipoRecomendacion } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsAnalisisMercadoCard {
  /** Datos del análisis de mercado */
  analisis: AnalisisMercado;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

function obtenerConfigRecomendacion(recomendacion: TipoRecomendacion) {
  switch (recomendacion) {
    case 'VALOR':
      return {
        icono: CheckCircle,
        texto: 'HAY VALOR',
        descripcion: 'La probabilidad del sistema supera significativamente la cuota',
        borderColor: 'border-neon-verde/30',
        bgColor: 'bg-neon-verde/10',
        textColor: 'text-neon-verde',
        glow: 'shadow-glow-verde',
      };
    case 'JUSTO':
      return {
        icono: MinusCircle,
        texto: 'PRECIO JUSTO',
        descripcion: 'La cuota refleja aproximadamente la probabilidad real',
        borderColor: 'border-advertencia-500/30',
        bgColor: 'bg-advertencia-500/10',
        textColor: 'text-advertencia-500',
        glow: '',
      };
    case 'EVITAR':
      return {
        icono: XCircle,
        texto: 'SIN VALOR',
        descripcion: 'La cuota no ofrece valor según el análisis',
        borderColor: 'border-neon-rojo/30',
        bgColor: 'bg-neon-rojo/10',
        textColor: 'text-neon-rojo',
        glow: 'shadow-glow-rojo',
      };
  }
}

function formatearPorcentaje(valor: number): string {
  const signo = valor >= 0 ? '+' : '';
  return `${signo}${(valor * 100).toFixed(1)}%`;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra el análisis de valor de mercado con estilo futurista
 */
export function AnalisisMercadoCard({ analisis }: PropsAnalisisMercadoCard) {
  const config = obtenerConfigRecomendacion(analisis.recomendacion);
  const Icono = config.icono;

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Recomendación principal */}
      <div className={`-m-6 mb-6 p-5 rounded-t-xl ${config.bgColor} ${config.borderColor} border-b`}>
        <div className="flex items-center gap-3">
          <Icono className={`${config.textColor} ${config.glow}`} size={28} />
          <div>
            <h3 className={`text-xl font-futurista font-bold tracking-wider ${config.textColor}`}>
              {config.texto}
            </h3>
            <p className="text-sm text-texto-secundario">
              {config.descripcion}
            </p>
          </div>
        </div>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-3 gap-4">
        {/* Edge */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <TrendingUp size={14} />
            <span className="text-xs uppercase tracking-wider">Edge</span>
          </div>
          <div className={`text-2xl font-mono font-bold ${
            analisis.edge >= 0 ? 'text-neon-verde texto-glow-verde' : 'text-neon-rojo texto-glow-rojo'
          }`}>
            {formatearPorcentaje(analisis.edge)}
          </div>
        </div>

        {/* Probabilidad Implícita */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <Percent size={14} />
            <span className="text-xs uppercase tracking-wider">Implícita</span>
          </div>
          <div className="text-2xl font-mono font-bold text-neon-cyan">
            {(analisis.probabilidad_implicita * 100).toFixed(1)}%
          </div>
        </div>

        {/* EV */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <Calculator size={14} />
            <span className="text-xs uppercase tracking-wider">EV</span>
          </div>
          <div className={`text-2xl font-mono font-bold ${
            analisis.valor_esperado >= 0 ? 'text-neon-verde' : 'text-neon-rojo'
          }`}>
            {analisis.valor_esperado >= 0 ? '+' : ''}{analisis.valor_esperado.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Nota explicativa */}
      <div className="mt-6 pt-4 border-t border-neon-cyan/10">
        <p className="text-xs text-texto-terciario">
          <span className="text-neon-cyan">Edge:</span> Diferencia entre probabilidad del sistema y la implícita.
          <span className="text-neon-cyan ml-2">EV:</span> Valor esperado por unidad.
          <span className="text-texto-secundario ml-2">Cuota: <span className="font-mono text-neon-cyan">{analisis.cuota.toFixed(2)}</span></span>
        </p>
      </div>
    </Tarjeta>
  );
}
