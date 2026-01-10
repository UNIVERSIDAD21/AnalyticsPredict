/**
 * TarjetaSizing.tsx — Muestra cuánto apostar y por qué (Kelly Criterion)
 *
 * Dos estados principales:
 * - Con bankroll: stake recomendado, porcentaje, detalles Kelly, caps
 * - Sin bankroll: Kelly fraccional como % guía + CTA para configurar
 */

import {
  DollarSign,
  Percent,
  TrendingUp,
  AlertTriangle,
  Settings,
  Shield,
  HelpCircle,
  Wallet,
} from 'lucide-react';
import { Tarjeta, Boton } from '../atomos';
import { PerfilRiesgo, PenalizacionesSizing } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaSizing {
  /** Kelly completo */
  kellyFull: number | null;

  /** Kelly fraccional (después de perfil y penalizaciones) */
  kellyFraccional: number | null;

  /** Fracción de kelly aplicada */
  fraccionKelly: number | null;

  /** Stake recomendado en moneda */
  stake: number | null;

  /** Stake como porcentaje del bankroll */
  stakePorcentaje: number | null;

  /** Bankroll en el momento del cálculo */
  bankroll: number | null;

  /** Perfil de riesgo usado */
  perfilRiesgo: PerfilRiesgo;

  /** Advertencias de sizing */
  advertencias: string[];

  /** Penalizaciones aplicadas */
  penalizaciones: PenalizacionesSizing;

  /** Callback para configurar bankroll (opcional) */
  onConfigurarBankroll?: () => void;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function obtenerConfigPerfil(perfil: PerfilRiesgo) {
  switch (perfil) {
    case 'CONSERVADOR':
      return {
        texto: 'Conservador',
        fraccion: '12.5%',
        color: 'text-neon-verde',
        bgColor: 'bg-neon-verde/10',
        borderColor: 'border-neon-verde/30',
      };
    case 'MEDIO':
      return {
        texto: 'Moderado',
        fraccion: '25%',
        color: 'text-neon-cyan',
        bgColor: 'bg-neon-cyan/10',
        borderColor: 'border-neon-cyan/30',
      };
    case 'AGRESIVO':
      return {
        texto: 'Agresivo',
        fraccion: '50%',
        color: 'text-neon-magenta',
        bgColor: 'bg-neon-magenta/10',
        borderColor: 'border-neon-magenta/30',
      };
  }
}

function formatearMoneda(valor: number | null): string {
  if (valor === null || !isFinite(valor)) return '—';
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(valor);
}

function formatearPorcentaje(valor: number | null, decimales = 2): string {
  if (valor === null || !isFinite(valor)) return '—';
  return `${(valor * 100).toFixed(decimales)}%`;
}

function obtenerTextoPenalizacion(key: string): string {
  const mapeo: Record<string, string> = {
    devig_estimado: 'De-vig estimado (×0.5)',
    devig_no_aplicado: 'Sin de-vig (×0.3)',
    riesgo_alto: 'Riesgo alto (×0.7)',
    kelly_negativo: 'Kelly negativo',
  };
  return mapeo[key] || key;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra el sizing recomendado basado en Kelly Criterion.
 */
export function TarjetaSizing({
  kellyFull,
  kellyFraccional,
  fraccionKelly,
  stake,
  stakePorcentaje,
  bankroll,
  perfilRiesgo,
  advertencias,
  penalizaciones,
  onConfigurarBankroll,
}: PropsTarjetaSizing) {
  const configPerfil = obtenerConfigPerfil(perfilRiesgo);
  const tieneBankroll = bankroll !== null && bankroll > 0;
  const kellyPositivo = kellyFull !== null && kellyFull > 0;

  // Si Kelly es negativo o cero, no se recomienda apostar
  if (!kellyPositivo) {
    return (
      <Tarjeta className="animate-deslizar-arriba">
        <div className="text-center py-6">
          <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-neon-rojo/10 border border-neon-rojo/30 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-neon-rojo" />
          </div>
          <h3 className="text-lg font-futurista font-bold text-neon-rojo mb-2">
            NO APOSTAR
          </h3>
          <p className="text-sm text-texto-secundario max-w-xs mx-auto">
            El criterio Kelly indica que esta apuesta no tiene valor esperado positivo.
            La fracción Kelly es {kellyFull !== null ? `${(kellyFull * 100).toFixed(2)}%` : 'negativa'}.
          </p>
          {advertencias.length > 0 && (
            <div className="mt-4 text-[10px] text-texto-terciario">
              {advertencias.join(' • ')}
            </div>
          )}
        </div>
      </Tarjeta>
    );
  }

  // Estado: Sin bankroll configurado
  if (!tieneBankroll) {
    return (
      <Tarjeta className="animate-deslizar-arriba">
        <div className="text-center py-4">
          <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center">
            <Wallet className="w-7 h-7 text-neon-cyan" />
          </div>
          <h3 className="text-lg font-futurista font-bold text-neon-cyan mb-2">
            SIZING DISPONIBLE
          </h3>
          <p className="text-sm text-texto-secundario max-w-xs mx-auto mb-4">
            Configura tu bankroll para ver el stake recomendado en dinero real.
          </p>

          {/* Kelly fraccional como guía */}
          <div className="inline-block p-4 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/20 mb-4">
            <div className="text-[10px] uppercase tracking-wider text-texto-terciario mb-1">
              Kelly Fraccional (% del bankroll)
            </div>
            <div className="text-3xl font-mono font-bold text-neon-cyan texto-glow-cyan">
              {formatearPorcentaje(kellyFraccional)}
            </div>
            <div className="text-[10px] text-texto-terciario mt-1">
              Perfil: {configPerfil.texto} ({configPerfil.fraccion} Kelly)
            </div>
          </div>

          {/* CTA para configurar bankroll */}
          {onConfigurarBankroll && (
            <Boton
              variante="secundario"
              iconoInicio={<Settings size={16} />}
              onClick={onConfigurarBankroll}
            >
              Configurar Bankroll
            </Boton>
          )}
        </div>
      </Tarjeta>
    );
  }

  // Estado: Con bankroll configurado - mostrar todo
  const penalizacionesActivas = Object.entries(penalizaciones).filter(
    ([, valor]) => valor !== undefined && valor < 1
  );

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Encabezado */}
      <div className={`-m-6 mb-5 p-4 rounded-t-xl ${configPerfil.bgColor} ${configPerfil.borderColor} border-b`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg ${configPerfil.bgColor} flex items-center justify-center border ${configPerfil.borderColor}`}>
              <DollarSign className={`w-5 h-5 ${configPerfil.color}`} />
            </div>
            <div>
              <h3 className={`text-sm font-futurista font-bold tracking-wider ${configPerfil.color}`}>
                SIZING RECOMENDADO
              </h3>
              <p className="text-xs text-texto-secundario">
                Perfil: {configPerfil.texto}
              </p>
            </div>
          </div>
          <div className="group relative">
            <HelpCircle size={16} className="text-texto-terciario cursor-help" />
            <div className="absolute bottom-full right-0 mb-2 w-64 p-3 rounded-lg bg-futurista-oscuro border border-neon-cyan/20 text-xs text-texto-secundario opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
              <strong className="text-neon-cyan">Kelly Criterion</strong> calcula el % óptimo del bankroll a apostar para maximizar crecimiento a largo plazo minimizando riesgo de ruina.
            </div>
          </div>
        </div>
      </div>

      {/* Stake prominente */}
      <div className="text-center mb-5">
        <div className="text-[10px] uppercase tracking-wider text-texto-terciario mb-1">
          Stake Recomendado
        </div>
        <div className="text-4xl font-mono font-bold text-neon-verde texto-glow-verde">
          {formatearMoneda(stake)}
        </div>
        <div className="text-sm text-texto-secundario mt-1">
          {formatearPorcentaje(stakePorcentaje)} de tu bankroll
        </div>
      </div>

      {/* Detalles Kelly */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {/* Bankroll */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <Wallet size={12} />
            <span className="text-[10px] uppercase tracking-wider">Bankroll</span>
          </div>
          <div className="text-lg font-mono font-bold text-texto-principal">
            {formatearMoneda(bankroll)}
          </div>
        </div>

        {/* Kelly Full */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <TrendingUp size={12} />
            <span className="text-[10px] uppercase tracking-wider">Kelly Full</span>
          </div>
          <div className="text-lg font-mono font-bold text-neon-cyan">
            {formatearPorcentaje(kellyFull)}
          </div>
        </div>

        {/* Fracción aplicada */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <Percent size={12} />
            <span className="text-[10px] uppercase tracking-wider">Fracción</span>
          </div>
          <div className={`text-lg font-mono font-bold ${configPerfil.color}`}>
            {formatearPorcentaje(fraccionKelly)}
          </div>
        </div>

        {/* Kelly Fraccional */}
        <div className="text-center p-3 rounded-lg bg-futurista-oscuro/30">
          <div className="flex items-center justify-center gap-1 text-texto-terciario mb-2">
            <Shield size={12} />
            <span className="text-[10px] uppercase tracking-wider">Kelly Frac.</span>
          </div>
          <div className="text-lg font-mono font-bold text-neon-verde">
            {formatearPorcentaje(kellyFraccional)}
          </div>
        </div>
      </div>

      {/* Penalizaciones aplicadas */}
      {penalizacionesActivas.length > 0 && (
        <div className="mb-4 p-3 rounded-lg bg-neon-amarillo/5 border border-neon-amarillo/20">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={14} className="text-neon-amarillo" />
            <span className="text-xs font-bold uppercase tracking-wider text-neon-amarillo">
              Ajustes Aplicados
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {penalizacionesActivas.map(([key]) => (
              <span
                key={key}
                className="px-2 py-1 text-[10px] uppercase font-bold rounded-full bg-neon-amarillo/15 text-neon-amarillo border border-neon-amarillo/30"
              >
                {obtenerTextoPenalizacion(key)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Advertencias */}
      {advertencias.length > 0 && (
        <div className="pt-3 border-t border-neon-cyan/10">
          <div className="flex items-start gap-2">
            <AlertTriangle size={12} className="text-texto-terciario mt-0.5 flex-shrink-0" />
            <div className="text-[10px] text-texto-terciario">
              {advertencias.map((adv, idx) => (
                <p key={idx}>{adv}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </Tarjeta>
  );
}
