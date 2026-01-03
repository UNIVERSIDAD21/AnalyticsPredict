/**
 * AnalisisMercadoCard.tsx — Muestra el análisis de valor cuando hay cuota
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
        texto: '¡Hay Valor!',
        descripcion: 'La probabilidad del sistema supera significativamente la cuota',
        colorFondo: 'bg-exito-50',
        colorTexto: 'text-exito-600',
        colorIcono: 'text-exito-500',
      };
    case 'JUSTO':
      return {
        icono: MinusCircle,
        texto: 'Precio Justo',
        descripcion: 'La cuota refleja aproximadamente la probabilidad real',
        colorFondo: 'bg-advertencia-50',
        colorTexto: 'text-advertencia-600',
        colorIcono: 'text-advertencia-500',
      };
    case 'EVITAR':
      return {
        icono: XCircle,
        texto: 'Sin Valor',
        descripcion: 'La cuota no ofrece valor según el análisis',
        colorFondo: 'bg-error-50',
        colorTexto: 'text-error-600',
        colorIcono: 'text-error-500',
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
 * Muestra el análisis de valor de mercado
 */
export function AnalisisMercadoCard({ analisis }: PropsAnalisisMercadoCard) {
  const config = obtenerConfigRecomendacion(analisis.recomendacion);
  const Icono = config.icono;

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Recomendación principal */}
      <div className={`${config.colorFondo} -m-6 mb-6 p-6 rounded-t-xl`}>
        <div className="flex items-center gap-3">
          <Icono className={config.colorIcono} size={32} />
          <div>
            <h3 className={`text-xl font-bold ${config.colorTexto}`}>
              {config.texto}
            </h3>
            <p className={`text-sm ${config.colorTexto} opacity-80`}>
              {config.descripcion}
            </p>
          </div>
        </div>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-3 gap-4">
        {/* Edge */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-nba-gris-500 mb-1">
            <TrendingUp size={16} />
            <span className="text-xs uppercase">Edge</span>
          </div>
          <div className={`text-2xl font-bold ${analisis.edge >= 0 ? 'text-exito-600' : 'text-error-600'}`}>
            {formatearPorcentaje(analisis.edge)}
          </div>
        </div>

        {/* Probabilidad Implícita */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-nba-gris-500 mb-1">
            <Percent size={16} />
            <span className="text-xs uppercase">Implícita</span>
          </div>
          <div className="text-2xl font-bold text-nba-gris-900">
            {(analisis.probabilidad_implicita * 100).toFixed(1)}%
          </div>
        </div>

        {/* EV */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-nba-gris-500 mb-1">
            <Calculator size={16} />
            <span className="text-xs uppercase">EV</span>
          </div>
          <div className={`text-2xl font-bold ${analisis.valor_esperado >= 0 ? 'text-exito-600' : 'text-error-600'}`}>
            {analisis.valor_esperado >= 0 ? '+' : ''}{analisis.valor_esperado.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Nota explicativa */}
      <div className="mt-6 pt-4 border-t border-nba-gris-200">
        <p className="text-xs text-nba-gris-500">
          <strong>Edge:</strong> Diferencia entre probabilidad del sistema y la implícita en la cuota.
          <strong> EV:</strong> Valor esperado por unidad apostada.
          Cuota analizada: <strong>{analisis.cuota.toFixed(2)}</strong>
        </p>
      </div>
    </Tarjeta>
  );
}
