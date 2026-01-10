/**
 * PaginaConfiguracion.tsx — Página de configuración de usuario
 */

import { useMemo, useState } from 'react';
import { ArrowLeft, Shield, Wallet, SlidersHorizontal } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton } from '../atomos';
import { useConfiguracionUsuario } from '../../contextos/ConfiguracionUsuario';
import { useToasts } from '../../contextos/Toasts';
import type { ConfiguracionUsuario, ModoDevig, PerfilRiesgo } from '../../tipos';

interface ErroresConfiguracion {
  bankroll?: string;
  capPorApuesta?: string;
  capDiario?: string;
  stakeMinimo?: string;
}

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

export function PaginaConfiguracion() {
  const { configuracion, actualizarConfiguracion } = useConfiguracionUsuario();
  const { agregarToast } = useToasts();

  const [sinBankroll, setSinBankroll] = useState(configuracion.bankroll === null);
  const [bankrollInput, setBankrollInput] = useState(
    configuracion.bankroll === null ? '' : configuracion.bankroll.toString()
  );
  const [perfilRiesgo, setPerfilRiesgo] = useState<PerfilRiesgo>(configuracion.perfilRiesgo);
  const [modoDevig, setModoDevig] = useState<ModoDevig>(configuracion.modoDevig);
  const [capPorApuesta, setCapPorApuesta] = useState(configuracion.capPorApuesta.toString());
  const [capDiario, setCapDiario] = useState(configuracion.capDiario.toString());
  const [stakeMinimo, setStakeMinimo] = useState(configuracion.stakeMinimo.toString());

  const { errores, valores, esValido } = useMemo(() => {
    const nuevosErrores: ErroresConfiguracion = {};

    const bankrollValor = sinBankroll ? null : Number(bankrollInput);
    if (!sinBankroll) {
      if (!bankrollInput.trim()) {
        nuevosErrores.bankroll = 'Debes ingresar un bankroll o activar modo demo.';
      } else if (!Number.isFinite(bankrollValor) || (bankrollValor ?? 0) <= 0) {
        nuevosErrores.bankroll = 'El bankroll debe ser un número mayor a 0.';
      }
    }

    const capPorApuestaValor = Number(capPorApuesta);
    if (!capPorApuesta.trim()) {
      nuevosErrores.capPorApuesta = 'Cap por apuesta requerido.';
    } else if (!Number.isFinite(capPorApuestaValor)) {
      nuevosErrores.capPorApuesta = 'Cap por apuesta inválido.';
    } else if (capPorApuestaValor < 0 || capPorApuestaValor > 100) {
      nuevosErrores.capPorApuesta = 'El cap por apuesta debe estar entre 0 y 100.';
    }

    const capDiarioValor = Number(capDiario);
    if (!capDiario.trim()) {
      nuevosErrores.capDiario = 'Cap diario requerido.';
    } else if (!Number.isFinite(capDiarioValor)) {
      nuevosErrores.capDiario = 'Cap diario inválido.';
    } else if (capDiarioValor < 0 || capDiarioValor > 100) {
      nuevosErrores.capDiario = 'El cap diario debe estar entre 0 y 100.';
    } else if (Number.isFinite(capPorApuestaValor) && capDiarioValor < capPorApuestaValor) {
      nuevosErrores.capDiario = 'El cap diario debe ser mayor o igual al cap por apuesta.';
    }

    const stakeMinimoValor = Number(stakeMinimo);
    if (!stakeMinimo.trim()) {
      nuevosErrores.stakeMinimo = 'Stake mínimo requerido.';
    } else if (!Number.isFinite(stakeMinimoValor)) {
      nuevosErrores.stakeMinimo = 'Stake mínimo inválido.';
    } else if (stakeMinimoValor < 0) {
      nuevosErrores.stakeMinimo = 'El stake mínimo no puede ser negativo.';
    } else if (
      bankrollValor !== null &&
      Number.isFinite(bankrollValor) &&
      stakeMinimoValor > bankrollValor
    ) {
      nuevosErrores.stakeMinimo = 'El stake mínimo no puede superar el bankroll.';
    }

    return {
      errores: nuevosErrores,
      esValido: Object.keys(nuevosErrores).length === 0,
      valores: {
        bankrollValor,
        capPorApuestaValor,
        capDiarioValor,
        stakeMinimoValor,
      },
    };
  }, [bankrollInput, capDiario, capPorApuesta, sinBankroll, stakeMinimo]);

  const guardarConfiguracion = () => {
    if (!esValido) {
      agregarToast({
        titulo: 'Revisa la configuración',
        mensaje: 'Corrige los campos resaltados antes de guardar.',
        tipo: 'error',
      });
      return;
    }

    const bankrollFinal = sinBankroll ? null : valores.bankrollValor;
    const huboCambioBankroll = bankrollFinal !== configuracion.bankroll;

    const historial = huboCambioBankroll
      ? [
        {
          timestamp: new Date().toISOString(),
          valor: bankrollFinal,
        },
        ...configuracion.bankrollHistorial,
      ]
      : configuracion.bankrollHistorial;

    const nuevaConfiguracion: ConfiguracionUsuario = {
      bankroll: bankrollFinal,
      perfilRiesgo,
      modoDevig,
      capPorApuesta: valores.capPorApuestaValor,
      capDiario: valores.capDiarioValor,
      stakeMinimo: valores.stakeMinimoValor,
      bankrollHistorial: historial,
    };

    actualizarConfiguracion(nuevaConfiguracion);
    agregarToast({
      titulo: 'Configuración guardada',
      mensaje: 'Tus preferencias se aplicarán en los próximos análisis.',
      tipo: 'success',
    });
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-futurista text-texto-principal">Configuración</h2>
            <p className="text-sm text-texto-secundario">
              Ajusta bankroll, perfil de riesgo y preferencias de análisis.
            </p>
          </div>
          <Boton variante="secundario" iconoInicio={<ArrowLeft size={16} />} onClick={() => navegar('/')}>
            Volver al análisis
          </Boton>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bankroll */}
          <div className="tarjeta p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center">
                <Wallet className="w-5 h-5 text-neon-cyan" />
              </div>
              <div>
                <h3 className="text-lg font-futurista text-texto-principal">Bankroll</h3>
                <p className="text-xs text-texto-secundario">
                  Define tu capital disponible para sizing real.
                </p>
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-texto-secundario">
              <input
                type="checkbox"
                checked={sinBankroll}
                onChange={(event) => setSinBankroll(event.target.checked)}
                className="accent-neon-cyan"
              />
              Sin bankroll (modo demo)
            </label>

            <div>
              <label className="text-xs uppercase tracking-widest text-texto-secundario">
                Bankroll actual (USD)
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                disabled={sinBankroll}
                value={bankrollInput}
                onChange={(event) => setBankrollInput(event.target.value)}
                className={`mt-2 w-full rounded-lg px-3 py-2 bg-futurista-oscuro/70 border ${
                  errores.bankroll ? 'border-neon-rojo/70' : 'border-neon-cyan/20'
                } text-texto-principal focus:outline-none focus:border-neon-cyan`}
                placeholder="Ej: 2500"
              />
              {errores.bankroll && (
                <p className="mt-1 text-xs text-neon-rojo">{errores.bankroll}</p>
              )}
            </div>

            <div className="border-t border-neon-cyan/10 pt-3">
              <p className="text-xs uppercase tracking-widest text-texto-secundario mb-2">
                Historial reciente
              </p>
              {configuracion.bankrollHistorial.length === 0 && (
                <p className="text-xs text-texto-terciario">
                  No hay cambios registrados aún.
                </p>
              )}
              {configuracion.bankrollHistorial.slice(0, 4).map((item) => (
                <div key={item.timestamp} className="flex justify-between text-xs text-texto-secundario">
                  <span>{new Date(item.timestamp).toLocaleString('es-ES')}</span>
                  <span className="font-mono">
                    {item.valor === null ? 'Demo' : `$${item.valor.toFixed(2)}`}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Perfil de riesgo */}
          <div className="tarjeta p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neon-verde/10 border border-neon-verde/30 flex items-center justify-center">
                <Shield className="w-5 h-5 text-neon-verde" />
              </div>
              <div>
                <h3 className="text-lg font-futurista text-texto-principal">Perfil de riesgo</h3>
                <p className="text-xs text-texto-secundario">
                  Ajusta la fracción de Kelly aplicada al sizing.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {(['CONSERVADOR', 'MEDIO', 'AGRESIVO'] as PerfilRiesgo[]).map((perfil) => (
                <button
                  key={perfil}
                  type="button"
                  onClick={() => setPerfilRiesgo(perfil)}
                  className={`px-4 py-3 rounded-lg border text-xs uppercase tracking-widest ${
                    perfilRiesgo === perfil
                      ? 'border-neon-cyan text-neon-cyan bg-neon-cyan/10'
                      : 'border-neon-cyan/20 text-texto-secundario'
                  }`}
                >
                  {perfil === 'CONSERVADOR' && 'Conservador'}
                  {perfil === 'MEDIO' && 'Medio'}
                  {perfil === 'AGRESIVO' && 'Agresivo'}
                </button>
              ))}
            </div>

            <p className="text-xs text-texto-terciario">
              Conservador aplica menor exposición, agresivo usa fracción Kelly más alta.
            </p>
          </div>

          {/* Preferencias de análisis */}
          <div className="tarjeta p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neon-magenta/10 border border-neon-magenta/30 flex items-center justify-center">
                <SlidersHorizontal className="w-5 h-5 text-neon-magenta" />
              </div>
              <div>
                <h3 className="text-lg font-futurista text-texto-principal">Preferencias de análisis</h3>
                <p className="text-xs text-texto-secundario">
                  Define el modo de de-vig por defecto.
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm text-texto-secundario">
                <input
                  type="radio"
                  name="modoDevig"
                  value="estricto"
                  checked={modoDevig === 'estricto'}
                  onChange={() => setModoDevig('estricto')}
                  className="accent-neon-magenta"
                />
                Estricto (requiere cuotas OVER y UNDER).
              </label>
              <label className="flex items-center gap-2 text-sm text-texto-secundario">
                <input
                  type="radio"
                  name="modoDevig"
                  value="estimado"
                  checked={modoDevig === 'estimado'}
                  onChange={() => setModoDevig('estimado')}
                  className="accent-neon-magenta"
                />
                Estimado (permite una cuota, aplica penalización).
              </label>
            </div>
          </div>

          {/* Caps de seguridad */}
          <div className="tarjeta p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center">
                <Shield className="w-5 h-5 text-neon-cyan" />
              </div>
              <div>
                <h3 className="text-lg font-futurista text-texto-principal">Caps de seguridad</h3>
                <p className="text-xs text-texto-secundario">
                  Estos límites se guardan, aún no impactan el cálculo actual.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs uppercase tracking-widest text-texto-secundario">
                  Cap por apuesta (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={capPorApuesta}
                  onChange={(event) => setCapPorApuesta(event.target.value)}
                  className={`mt-2 w-full rounded-lg px-3 py-2 bg-futurista-oscuro/70 border ${
                    errores.capPorApuesta ? 'border-neon-rojo/70' : 'border-neon-cyan/20'
                  } text-texto-principal focus:outline-none focus:border-neon-cyan`}
                />
                {errores.capPorApuesta && (
                  <p className="mt-1 text-xs text-neon-rojo">{errores.capPorApuesta}</p>
                )}
              </div>

              <div>
                <label className="text-xs uppercase tracking-widest text-texto-secundario">
                  Cap diario (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={capDiario}
                  onChange={(event) => setCapDiario(event.target.value)}
                  className={`mt-2 w-full rounded-lg px-3 py-2 bg-futurista-oscuro/70 border ${
                    errores.capDiario ? 'border-neon-rojo/70' : 'border-neon-cyan/20'
                  } text-texto-principal focus:outline-none focus:border-neon-cyan`}
                />
                {errores.capDiario && (
                  <p className="mt-1 text-xs text-neon-rojo">{errores.capDiario}</p>
                )}
              </div>

              <div>
                <label className="text-xs uppercase tracking-widest text-texto-secundario">
                  Stake mínimo (USD)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={stakeMinimo}
                  onChange={(event) => setStakeMinimo(event.target.value)}
                  className={`mt-2 w-full rounded-lg px-3 py-2 bg-futurista-oscuro/70 border ${
                    errores.stakeMinimo ? 'border-neon-rojo/70' : 'border-neon-cyan/20'
                  } text-texto-principal focus:outline-none focus:border-neon-cyan`}
                />
                {errores.stakeMinimo && (
                  <p className="mt-1 text-xs text-neon-rojo">{errores.stakeMinimo}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Boton variante="primario" onClick={guardarConfiguracion} disabled={!esValido}>
            Guardar configuración
          </Boton>
          {!esValido && (
            <p className="text-xs text-neon-rojo self-center">
              Corrige los campos resaltados para guardar.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
