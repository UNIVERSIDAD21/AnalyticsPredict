import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { Crown, Lock, Sparkles, UserPlus, X } from 'lucide-react';
import { Boton } from '../componentes/atomos';
import type { TipoGate } from '../servicios/accessPolicy';

interface GatePromptOptions {
  tipoGate: TipoGate;
  titulo: string;
  mensaje: string;
  accionPrincipalLabel: string;
  accionSecundariaLabel?: string;
  onAccionPrincipal: () => void;
  onAccionSecundaria?: () => void;
}

interface GatePromptContextType {
  abrirGatePrompt: (options: GatePromptOptions) => void;
  cerrarGatePrompt: () => void;
}

interface GatePromptState extends GatePromptOptions {
  abierto: boolean;
}

const GatePromptContext = createContext<GatePromptContextType | undefined>(undefined);

function resolverEstiloGate(tipoGate: TipoGate) {
  if (tipoGate === 'PREMIUM_REQUIRED') {
    return {
      etiqueta: 'Bloqueo Premium',
      icono: Crown,
      borde: 'border-neon-magenta/30',
      cajaIcono: 'border-neon-magenta/30 bg-neon-magenta/10',
      iconoColor: 'text-neon-magenta',
      ayuda: 'Premium aporta profundidad operativa: más contexto, histórico extendido y comparativas avanzadas.',
    };
  }

  if (tipoGate === 'BASE_REQUIRED') {
    return {
      etiqueta: 'Bloqueo de cuenta',
      icono: UserPlus,
      borde: 'border-neon-cyan/30',
      cajaIcono: 'border-neon-cyan/30 bg-neon-cyan/10',
      iconoColor: 'text-neon-cyan',
      ayuda: 'Crear cuenta desbloquea continuidad personal: análisis, bitácora, dashboard y configuración base.',
    };
  }

  return {
    etiqueta: 'Fuera de alcance',
    icono: Lock,
    borde: 'border-advertencia-500/40',
    cajaIcono: 'border-advertencia-500/40 bg-advertencia-500/10',
    iconoColor: 'text-advertencia-500',
    ayuda: 'Esta capacidad no está habilitada en la fase actual.',
  };
}

export function ProveedorGatePrompt({ children }: { children: ReactNode }) {
  const [state, setState] = useState<GatePromptState | null>(null);

  const cerrarGatePrompt = useCallback(() => {
    setState(null);
  }, []);

  const abrirGatePrompt = useCallback((options: GatePromptOptions) => {
    setState({ ...options, abierto: true });
  }, []);

  const value = useMemo(
    () => ({ abrirGatePrompt, cerrarGatePrompt }),
    [abrirGatePrompt, cerrarGatePrompt]
  );

  const handlePrincipal = () => {
    if (!state) return;
    state.onAccionPrincipal();
    cerrarGatePrompt();
  };

  const handleSecundaria = () => {
    if (!state) return;
    state.onAccionSecundaria?.();
    cerrarGatePrompt();
  };

  const estilo = state ? resolverEstiloGate(state.tipoGate) : null;
  const Icono = estilo?.icono ?? Lock;

  return (
    <GatePromptContext.Provider value={value}>
      {children}

      {state?.abierto && estilo && (
        <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-futurista-negro/80 backdrop-blur-sm"
            onClick={cerrarGatePrompt}
            aria-label="Cerrar"
          />

          <div className={`relative w-full max-w-lg rounded-2xl border ${estilo.borde} bg-futurista-oscuro/95 p-5 md:p-6 shadow-glow-cyan`}>
            <button
              type="button"
              onClick={cerrarGatePrompt}
              className="absolute right-3 top-3 text-texto-secundario hover:text-texto-principal"
              aria-label="Cerrar"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-start gap-3 pr-6">
              <div className={`mt-0.5 rounded-lg border p-2 ${estilo.cajaIcono}`}>
                <Icono className={`w-4 h-4 ${estilo.iconoColor}`} />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-neon-cyan">{estilo.etiqueta}</p>
                <h3 className="mt-1 text-xl font-futurista text-texto-principal">{state.titulo}</h3>
                <p className="mt-2 text-sm text-texto-secundario">{state.mensaje}</p>
              </div>
            </div>

            <div className="mt-5 rounded-lg border border-neon-cyan/20 bg-futurista-negro/40 p-3 text-xs text-texto-secundario flex items-start gap-2">
              <Sparkles className="w-4 h-4 text-neon-cyan mt-0.5" />
              {estilo.ayuda}
            </div>

            <div className="mt-5 flex flex-wrap gap-2">
              <Boton variante="primario" onClick={handlePrincipal}>
                {state.accionPrincipalLabel}
              </Boton>
              {state.accionSecundariaLabel && (
                <Boton variante="secundario" onClick={handleSecundaria}>
                  {state.accionSecundariaLabel}
                </Boton>
              )}
              <Boton variante="fantasma" onClick={cerrarGatePrompt}>
                Cerrar
              </Boton>
            </div>
          </div>
        </div>
      )}
    </GatePromptContext.Provider>
  );
}

export function useGatePrompt() {
  const ctx = useContext(GatePromptContext);
  if (!ctx) {
    throw new Error('useGatePrompt debe usarse dentro de ProveedorGatePrompt');
  }
  return ctx;
}
