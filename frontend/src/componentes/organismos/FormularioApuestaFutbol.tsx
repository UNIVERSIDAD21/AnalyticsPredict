/**
 * FormularioApuestaFutbol.tsx — Formulario de apuestas de fútbol
 *
 * Formulario completo para registrar apuestas de fútbol con:
 * - Selector de mercado con los 24 mercados agrupados por categoría
 * - Inputs de línea, cuota y stake
 * - Toggle OVER/UNDER
 * - Selector de casa de apuestas
 * - Notas opcionales
 * - Cálculo de ganancias potenciales
 * - Diseño futurista con colores neón
 */

import { useCallback, useMemo, useState } from 'react';
import {
  Target,
  CornerUpRight,
  Crosshair,
  Calculator,
  FileText,
  Building2,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  RotateCcw,
  Save,
} from 'lucide-react';
import { clsx } from 'clsx';
import {
  TipoMercadoFutbol,
  MERCADOS_CORNERS,
  MERCADOS_GOLES,
  MERCADOS_DISPAROS,
  ETIQUETAS_MERCADOS,
  CASAS_APUESTAS,
} from '../../tipos/futbol';
import { Boton, Input, Tarjeta } from '../atomos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsFormularioApuestaFutbol {
  /** ID del partido (si ya está seleccionado) */
  partidoId?: string;
  /** Nombre del partido para mostrar */
  nombrePartido?: string;
  /** Callback al enviar el formulario */
  onSubmit: (datos: DatosApuestaFutbol) => void;
  /** Callback al cancelar */
  onCancelar?: () => void;
  /** Indica si está cargando */
  cargando?: boolean;
  /** Valores iniciales (para edición) */
  valoresIniciales?: Partial<DatosApuestaFutbol>;
  /** Clase CSS adicional */
  className?: string;
}

export interface DatosApuestaFutbol {
  partidoId: string;
  mercado: TipoMercadoFutbol;
  lado: 'OVER' | 'UNDER';
  linea: number;
  cuota: number;
  stake: number;
  casaApuestas: string;
  notas?: string;
}

interface EstadoFormulario {
  mercado: TipoMercadoFutbol | '';
  lado: 'OVER' | 'UNDER';
  linea: string;
  cuota: string;
  stake: string;
  casaApuestas: string;
  notas: string;
}

interface GrupoMercado {
  id: string;
  nombre: string;
  icono: React.ReactNode;
  mercados: TipoMercadoFutbol[];
  colorActivo: string;
  colorFondo: string;
}

// ══════════════════════════════════════════════════════════════
// CONSTANTES
// ══════════════════════════════════════════════════════════════

const GRUPOS_MERCADOS: GrupoMercado[] = [
  {
    id: 'corners',
    nombre: 'Corners',
    icono: <CornerUpRight size={16} />,
    mercados: MERCADOS_CORNERS,
    colorActivo: 'neon-cyan',
    colorFondo: 'neon-cyan/10',
  },
  {
    id: 'goles',
    nombre: 'Goles',
    icono: <Target size={16} />,
    mercados: MERCADOS_GOLES,
    colorActivo: 'neon-verde',
    colorFondo: 'neon-verde/10',
  },
  {
    id: 'disparos',
    nombre: 'Disparos',
    icono: <Crosshair size={16} />,
    mercados: MERCADOS_DISPAROS,
    colorActivo: 'neon-amarillo',
    colorFondo: 'neon-amarillo/10',
  },
];

const ESTADO_INICIAL: EstadoFormulario = {
  mercado: '',
  lado: 'OVER',
  linea: '',
  cuota: '',
  stake: '',
  casaApuestas: '',
  notas: '',
};

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/**
 * Valida una cuota
 */
function validarCuota(valor: string): boolean {
  const num = parseFloat(valor);
  return !isNaN(num) && num >= 1.01;
}

/**
 * Valida una línea
 */
function validarLinea(valor: string): boolean {
  const num = parseFloat(valor);
  return !isNaN(num) && num >= 0;
}

/**
 * Valida un stake
 */
function validarStake(valor: string): boolean {
  const num = parseFloat(valor);
  return !isNaN(num) && num > 0;
}

/**
 * Calcula las ganancias potenciales
 */
function calcularGananciasPotenciales(stake: number, cuota: number): number {
  return stake * (cuota - 1);
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE SELECTOR DE MERCADO
// ══════════════════════════════════════════════════════════════

interface PropsSelectorMercadoFutbol {
  valor: TipoMercadoFutbol | '';
  onChange: (mercado: TipoMercadoFutbol) => void;
  deshabilitado?: boolean;
}

function SelectorMercadoFutbol({ valor, onChange, deshabilitado }: PropsSelectorMercadoFutbol) {
  const [grupoExpandido, setGrupoExpandido] = useState<string | null>(null);

  // Encontrar a qué grupo pertenece el mercado seleccionado
  const grupoSeleccionado = useMemo(() => {
    if (!valor) return null;
    return GRUPOS_MERCADOS.find((g) => g.mercados.includes(valor as TipoMercadoFutbol));
  }, [valor]);

  return (
    <div className="space-y-3">
      <label className="etiqueta flex items-center gap-2">
        <Target size={14} className="text-neon-cyan" />
        Mercado
      </label>

      {/* Grupos de mercados */}
      <div className="grid grid-cols-3 gap-2">
        {GRUPOS_MERCADOS.map((grupo) => {
          const estaExpandido = grupoExpandido === grupo.id;
          const tieneSeleccion = grupoSeleccionado?.id === grupo.id;

          return (
            <button
              key={grupo.id}
              type="button"
              onClick={() => setGrupoExpandido(estaExpandido ? null : grupo.id)}
              disabled={deshabilitado}
              className={clsx(
                'flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-semibold transition-all',
                estaExpandido || tieneSeleccion
                  ? `bg-${grupo.colorFondo} border-${grupo.colorActivo}/50 text-${grupo.colorActivo}`
                  : 'bg-futurista-oscuro/50 border-neon-cyan/20 text-texto-secundario hover:text-texto-principal hover:border-neon-cyan/30',
                deshabilitado && 'opacity-50 cursor-not-allowed'
              )}
              style={{
                backgroundColor: estaExpandido || tieneSeleccion
                  ? grupo.id === 'corners' ? 'rgba(34, 211, 238, 0.1)'
                    : grupo.id === 'goles' ? 'rgba(16, 185, 129, 0.1)'
                    : 'rgba(245, 158, 11, 0.1)'
                  : undefined,
                borderColor: estaExpandido || tieneSeleccion
                  ? grupo.id === 'corners' ? 'rgba(34, 211, 238, 0.5)'
                    : grupo.id === 'goles' ? 'rgba(16, 185, 129, 0.5)'
                    : 'rgba(245, 158, 11, 0.5)'
                  : undefined,
                color: estaExpandido || tieneSeleccion
                  ? grupo.id === 'corners' ? '#22d3ee'
                    : grupo.id === 'goles' ? '#10b981'
                    : '#f59e0b'
                  : undefined,
              }}
            >
              {grupo.icono}
              <span>{grupo.nombre}</span>
              {tieneSeleccion && !estaExpandido && (
                <span className="w-2 h-2 rounded-full bg-current" />
              )}
            </button>
          );
        })}
      </div>

      {/* Lista de mercados del grupo expandido */}
      {grupoExpandido && (
        <div className="p-3 rounded-lg bg-futurista-oscuro/50 border border-neon-cyan/10 animate-entrada">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {GRUPOS_MERCADOS.find((g) => g.id === grupoExpandido)?.mercados.map((mercado) => {
              const estaSeleccionado = valor === mercado;
              const grupo = GRUPOS_MERCADOS.find((g) => g.id === grupoExpandido)!;

              return (
                <button
                  key={mercado}
                  type="button"
                  onClick={() => {
                    onChange(mercado);
                    setGrupoExpandido(null);
                  }}
                  disabled={deshabilitado}
                  className={clsx(
                    'px-3 py-2 rounded-lg text-xs font-medium text-left transition-all border',
                    estaSeleccionado
                      ? 'border-current'
                      : 'border-transparent hover:bg-futurista-medio/50',
                    deshabilitado && 'opacity-50 cursor-not-allowed'
                  )}
                  style={{
                    backgroundColor: estaSeleccionado
                      ? grupo.id === 'corners' ? 'rgba(34, 211, 238, 0.2)'
                        : grupo.id === 'goles' ? 'rgba(16, 185, 129, 0.2)'
                        : 'rgba(245, 158, 11, 0.2)'
                      : undefined,
                    color: estaSeleccionado
                      ? grupo.id === 'corners' ? '#22d3ee'
                        : grupo.id === 'goles' ? '#10b981'
                        : '#f59e0b'
                      : undefined,
                  }}
                >
                  {ETIQUETAS_MERCADOS[mercado]}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Mercado seleccionado */}
      {valor && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-texto-terciario">Seleccionado:</span>
          <span
            className="font-semibold"
            style={{
              color: grupoSeleccionado?.id === 'corners' ? '#22d3ee'
                : grupoSeleccionado?.id === 'goles' ? '#10b981'
                : '#f59e0b',
            }}
          >
            {ETIQUETAS_MERCADOS[valor]}
          </span>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE TOGGLE OVER/UNDER
// ══════════════════════════════════════════════════════════════

interface PropsToggleLado {
  valor: 'OVER' | 'UNDER';
  onChange: (lado: 'OVER' | 'UNDER') => void;
  deshabilitado?: boolean;
}

function ToggleLado({ valor, onChange, deshabilitado }: PropsToggleLado) {
  return (
    <div className="space-y-2">
      <label className="etiqueta">Lado</label>
      <div className="flex rounded-lg overflow-hidden border border-neon-cyan/20">
        <button
          type="button"
          onClick={() => onChange('OVER')}
          disabled={deshabilitado}
          className={clsx(
            'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold transition-all',
            valor === 'OVER'
              ? 'bg-neon-verde/20 text-neon-verde border-r border-neon-verde/30'
              : 'bg-futurista-oscuro/50 text-texto-terciario hover:text-texto-secundario border-r border-neon-cyan/20',
            deshabilitado && 'opacity-50 cursor-not-allowed'
          )}
        >
          <ArrowUpRight size={18} />
          OVER
        </button>
        <button
          type="button"
          onClick={() => onChange('UNDER')}
          disabled={deshabilitado}
          className={clsx(
            'flex-1 flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold transition-all',
            valor === 'UNDER'
              ? 'bg-neon-magenta/20 text-neon-magenta'
              : 'bg-futurista-oscuro/50 text-texto-terciario hover:text-texto-secundario',
            deshabilitado && 'opacity-50 cursor-not-allowed'
          )}
        >
          <ArrowDownRight size={18} />
          UNDER
        </button>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Formulario completo para registrar apuestas de fútbol
 */
export function FormularioApuestaFutbol({
  partidoId,
  nombrePartido,
  onSubmit,
  onCancelar,
  cargando = false,
  valoresIniciales,
  className,
}: PropsFormularioApuestaFutbol) {
  // Estado del formulario
  const [formulario, setFormulario] = useState<EstadoFormulario>(() => ({
    ...ESTADO_INICIAL,
    mercado: valoresIniciales?.mercado || '',
    lado: valoresIniciales?.lado || 'OVER',
    linea: valoresIniciales?.linea?.toString() || '',
    cuota: valoresIniciales?.cuota?.toString() || '',
    stake: valoresIniciales?.stake?.toString() || '',
    casaApuestas: valoresIniciales?.casaApuestas || '',
    notas: valoresIniciales?.notas || '',
  }));

  const [errores, setErrores] = useState<Record<string, string>>({});

  // Actualizar campo del formulario
  const actualizarCampo = useCallback(
    <K extends keyof EstadoFormulario>(campo: K, valor: EstadoFormulario[K]) => {
      setFormulario((prev) => ({ ...prev, [campo]: valor }));
      // Limpiar error del campo
      if (errores[campo]) {
        setErrores((prev) => {
          const nuevo = { ...prev };
          delete nuevo[campo];
          return nuevo;
        });
      }
    },
    [errores]
  );

  // Resetear formulario
  const resetearFormulario = useCallback(() => {
    setFormulario(ESTADO_INICIAL);
    setErrores({});
  }, []);

  // Calcular ganancias potenciales
  const gananciasPotenciales = useMemo(() => {
    const stake = parseFloat(formulario.stake);
    const cuota = parseFloat(formulario.cuota);

    if (isNaN(stake) || isNaN(cuota) || stake <= 0 || cuota < 1.01) {
      return null;
    }

    return calcularGananciasPotenciales(stake, cuota);
  }, [formulario.stake, formulario.cuota]);

  // Validar y enviar
  const manejarEnvio = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();

      const nuevosErrores: Record<string, string> = {};

      // Validar partido
      if (!partidoId) {
        nuevosErrores.partido = 'Debes seleccionar un partido';
      }

      // Validar mercado
      if (!formulario.mercado) {
        nuevosErrores.mercado = 'Selecciona un mercado';
      }

      // Validar línea
      if (!formulario.linea || !validarLinea(formulario.linea)) {
        nuevosErrores.linea = 'Ingresa una linea valida (>= 0)';
      }

      // Validar cuota
      if (!formulario.cuota || !validarCuota(formulario.cuota)) {
        nuevosErrores.cuota = 'Ingresa una cuota valida (>= 1.01)';
      }

      // Validar stake
      if (!formulario.stake || !validarStake(formulario.stake)) {
        nuevosErrores.stake = 'Ingresa un stake valido (> 0)';
      }

      // Validar casa de apuestas
      if (!formulario.casaApuestas) {
        nuevosErrores.casaApuestas = 'Selecciona una casa de apuestas';
      }

      if (Object.keys(nuevosErrores).length > 0) {
        setErrores(nuevosErrores);
        return;
      }

      // Enviar datos
      onSubmit({
        partidoId: partidoId!,
        mercado: formulario.mercado as TipoMercadoFutbol,
        lado: formulario.lado,
        linea: parseFloat(formulario.linea),
        cuota: parseFloat(formulario.cuota),
        stake: parseFloat(formulario.stake),
        casaApuestas: formulario.casaApuestas,
        notas: formulario.notas.trim() || undefined,
      });
    },
    [formulario, partidoId, onSubmit]
  );

  return (
    <Tarjeta className={clsx('animate-entrada', className)}>
      <form onSubmit={manejarEnvio} className="space-y-6">
        {/* Header */}
        <div className="pb-4 border-b border-neon-cyan/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-neon-magenta/10 border border-neon-magenta/30 flex items-center justify-center">
              <Zap className="w-5 h-5 text-neon-magenta" />
            </div>
            <div>
              <h2 className="text-lg font-futurista font-bold text-texto-principal tracking-wider">
                REGISTRAR APUESTA
              </h2>
              {nombrePartido && (
                <p className="text-xs text-texto-secundario truncate max-w-[280px]">
                  {nombrePartido}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Error de partido */}
        {errores.partido && (
          <div className="p-3 rounded-lg bg-neon-rojo/10 border border-neon-rojo/30 text-neon-rojo text-sm">
            {errores.partido}
          </div>
        )}

        {/* Selector de mercado */}
        <SelectorMercadoFutbol
          valor={formulario.mercado}
          onChange={(mercado) => actualizarCampo('mercado', mercado)}
          deshabilitado={cargando}
        />
        {errores.mercado && (
          <p className="text-xs text-neon-rojo -mt-2">{errores.mercado}</p>
        )}

        {/* Toggle OVER/UNDER */}
        <ToggleLado
          valor={formulario.lado}
          onChange={(lado) => actualizarCampo('lado', lado)}
          deshabilitado={cargando}
        />

        {/* Inputs numéricos */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Linea */}
          <Input
            etiqueta="Linea"
            type="number"
            step="0.5"
            min="0"
            value={formulario.linea}
            onChange={(e) => actualizarCampo('linea', e.target.value)}
            placeholder="9.5"
            error={errores.linea}
            disabled={cargando}
          />

          {/* Cuota */}
          <Input
            etiqueta="Cuota"
            type="number"
            step="0.01"
            min="1.01"
            value={formulario.cuota}
            onChange={(e) => actualizarCampo('cuota', e.target.value)}
            placeholder="1.90"
            error={errores.cuota}
            disabled={cargando}
          />

          {/* Stake */}
          <Input
            etiqueta="Stake ($)"
            type="number"
            step="0.01"
            min="0"
            value={formulario.stake}
            onChange={(e) => actualizarCampo('stake', e.target.value)}
            placeholder="100"
            error={errores.stake}
            disabled={cargando}
            iconoInicio={<Calculator size={16} />}
          />
        </div>

        {/* Casa de apuestas */}
        <div className="space-y-2">
          <label className="etiqueta flex items-center gap-2">
            <Building2 size={14} className="text-neon-cyan" />
            Casa de Apuestas
          </label>
          <select
            value={formulario.casaApuestas}
            onChange={(e) => actualizarCampo('casaApuestas', e.target.value)}
            disabled={cargando}
            className={clsx(
              'select-base',
              errores.casaApuestas && 'input-error'
            )}
          >
            <option value="">Selecciona una casa</option>
            {CASAS_APUESTAS.map((casa) => (
              <option key={casa} value={casa}>
                {casa}
              </option>
            ))}
          </select>
          {errores.casaApuestas && (
            <p className="texto-error">{errores.casaApuestas}</p>
          )}
        </div>

        {/* Notas */}
        <div className="space-y-2">
          <label className="etiqueta flex items-center gap-2">
            <FileText size={14} className="text-neon-cyan" />
            Notas (opcional)
          </label>
          <textarea
            value={formulario.notas}
            onChange={(e) => actualizarCampo('notas', e.target.value)}
            placeholder="Razon de la apuesta, contexto del partido, etc."
            disabled={cargando}
            rows={3}
            className="input-base resize-none"
          />
        </div>

        {/* Resumen de ganancias potenciales */}
        {gananciasPotenciales !== null && (
          <div className="p-4 rounded-lg bg-gradient-to-r from-neon-verde/10 to-neon-cyan/10 border border-neon-verde/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-texto-terciario uppercase tracking-wider mb-1">
                  Ganancias Potenciales
                </p>
                <p className="text-2xl font-mono font-bold text-neon-verde">
                  +${gananciasPotenciales.toFixed(2)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-texto-terciario mb-1">Retorno total</p>
                <p className="text-lg font-mono font-semibold text-texto-principal">
                  ${(gananciasPotenciales + parseFloat(formulario.stake)).toFixed(2)}
                </p>
              </div>
            </div>

            {/* Resumen de la apuesta */}
            <div className="mt-3 pt-3 border-t border-neon-verde/20 text-sm text-texto-secundario">
              <span
                className={clsx(
                  'font-semibold',
                  formulario.lado === 'OVER' ? 'text-neon-verde' : 'text-neon-magenta'
                )}
              >
                {formulario.lado}
              </span>{' '}
              {formulario.linea}{' '}
              {formulario.mercado && (
                <span className="text-neon-cyan">
                  {ETIQUETAS_MERCADOS[formulario.mercado as TipoMercadoFutbol]}
                </span>
              )}{' '}
              @ {parseFloat(formulario.cuota).toFixed(2)}
            </div>
          </div>
        )}

        {/* Botones */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-neon-cyan/20">
          <Boton
            type="submit"
            variante="primario"
            tamano="lg"
            cargando={cargando}
            textoCargando="Guardando..."
            iconoInicio={<Save size={18} />}
            anchoCompleto
          >
            Guardar Apuesta
          </Boton>

          <div className="flex gap-3 sm:w-auto">
            <Boton
              type="button"
              variante="secundario"
              tamano="lg"
              onClick={resetearFormulario}
              disabled={cargando}
              iconoInicio={<RotateCcw size={18} />}
              className="flex-1 sm:flex-none"
            >
              Limpiar
            </Boton>

            {onCancelar && (
              <Boton
                type="button"
                variante="fantasma"
                tamano="lg"
                onClick={onCancelar}
                disabled={cargando}
                className="flex-1 sm:flex-none"
              >
                Cancelar
              </Boton>
            )}
          </div>
        </div>
      </form>
    </Tarjeta>
  );
}
