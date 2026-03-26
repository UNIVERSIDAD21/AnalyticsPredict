/**
 * PaginaConfiguracion.tsx — Página de configuración de usuario
 */

import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Shield, Wallet, SlidersHorizontal, Crown, Radar } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton } from '../atomos';
import { useConfiguracionUsuario } from '../../contextos/ConfiguracionUsuario';
import { useToasts } from '../../contextos/Toasts';
import type { ConfiguracionUsuario, ModoDevig, PerfilRiesgo } from '../../tipos';
import {
  enviarPruebaNotificacion,
  guardarPreferenciasNotificaciones,
  obtenerMetricasEntrega,
  obtenerPreferenciasNotificaciones,
  type MetricasEntregaNotificaciones,
  type PreferenciasNotificaciones,
} from '../../servicios/notificaciones';
import { obtenerEstadoPlan, type EstadoPlanUsuario } from '../../servicios/pagos';

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
  const [cargandoNotificaciones, setCargandoNotificaciones] = useState(true);
  const [guardandoNotificaciones, setGuardandoNotificaciones] = useState(false);
  const [metricasEntrega, setMetricasEntrega] = useState<MetricasEntregaNotificaciones | null>(null);
  const [prefsNotificaciones, setPrefsNotificaciones] = useState<PreferenciasNotificaciones>({
    email_habilitado: true,
    alertas_partidos: true,
    alertas_suscripcion: true,
    resumen_semanal: false,
  });
  const [estadoPlan, setEstadoPlan] = useState<EstadoPlanUsuario>({
    activo: false,
    planId: null,
    estado: null,
    actualizadoEn: null,
  });

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

  const recargarMetricasEntrega = async () => {
    try {
      const metricas = await obtenerMetricasEntrega(24);
      setMetricasEntrega(metricas);
    } catch {
      setMetricasEntrega(null);
    }
  };

  useEffect(() => {
    const cargarPreferencias = async () => {
      try {
        const [prefs, metricas, plan] = await Promise.all([
          obtenerPreferenciasNotificaciones(),
          obtenerMetricasEntrega(24),
          obtenerEstadoPlan(),
        ]);
        setPrefsNotificaciones(prefs.preferencias);
        setMetricasEntrega(metricas);
        setEstadoPlan(plan);
      } catch (error) {
        agregarToast({
          titulo: 'No se pudieron cargar notificaciones',
          mensaje: error instanceof Error ? error.message : 'Intenta nuevamente en unos segundos.',
          tipo: 'error',
        });
      } finally {
        setCargandoNotificaciones(false);
      }
    };

    void cargarPreferencias();
  }, [agregarToast]);

  const actualizarPreferencia = (campo: keyof PreferenciasNotificaciones, valor: boolean) => {
    setPrefsNotificaciones((prev) => ({ ...prev, [campo]: valor }));
  };

  const guardarNotificaciones = async () => {
    try {
      setGuardandoNotificaciones(true);
      const data = await guardarPreferenciasNotificaciones(prefsNotificaciones);
      setPrefsNotificaciones(data.preferencias);
      agregarToast({
        titulo: 'Notificaciones actualizadas',
        mensaje: 'Tus preferencias de alertas fueron guardadas.',
        tipo: 'success',
      });
      await recargarMetricasEntrega();
    } catch (error) {
      agregarToast({
        titulo: 'Error guardando notificaciones',
        mensaje: error instanceof Error ? error.message : 'Intenta de nuevo.',
        tipo: 'error',
      });
    } finally {
      setGuardandoNotificaciones(false);
    }
  };

  const probarNotificaciones = async () => {
    try {
      const result = await enviarPruebaNotificacion('alertas_partidos');
      agregarToast({
        titulo: 'Prueba enviada',
        mensaje: `Estado: ${result?.estado ?? 'desconocido'}`,
        tipo: 'success',
      });
      await recargarMetricasEntrega();
    } catch (error) {
      agregarToast({
        titulo: 'Falló la prueba',
        mensaje: error instanceof Error ? error.message : 'No se pudo enviar la prueba.',
        tipo: 'error',
      });
    }
  };

  const estadoEntrega = useMemo(() => {
    const tasa = metricasEntrega?.tasa_entrega_pct;
    if (tasa === null || tasa === undefined) {
      return { etiqueta: 'Sin datos', color: 'text-texto-terciario border-neon-cyan/20' };
    }
    if (tasa >= 90) {
      return { etiqueta: 'Verde', color: 'text-neon-verde border-neon-verde/40' };
    }
    if (tasa >= 70) {
      return { etiqueta: 'Amarillo', color: 'text-yellow-400 border-yellow-400/40' };
    }
    return { etiqueta: 'Rojo', color: 'text-neon-rojo border-neon-rojo/40' };
  }, [metricasEntrega]);

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
    navegar('/');
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
          <div className="tarjeta p-6 space-y-3 border border-neon-amarillo/30">
            <div className="flex items-center gap-2 text-neon-amarillo">
              <Radar className="w-4 h-4" />
              <h3 className="text-sm uppercase tracking-wider">Contexto fútbol (gobernanza)</h3>
            </div>
            <p className="text-sm text-texto-secundario">
              Fútbol incrementa peso por evidencia por competición. No se promociona con paridad comercial respecto a NBA hasta cumplir madurez.
            </p>
            <ul className="text-xs text-texto-terciario space-y-1">
              <li>• ESTABLE: despliegue normal de señal.</li>
              <li>• EN VALIDACIÓN: seguimiento y calibración activa.</li>
              <li>• LAB: uso controlado, sin promesa comercial fuerte.</li>
            </ul>
          </div>

          <div className="tarjeta p-6 space-y-3 border border-neon-magenta/30">
            <div className="flex items-center gap-2 text-neon-magenta">
              <Crown className="w-4 h-4" />
              <h3 className="text-sm uppercase tracking-wider">Estado de plan y capa premium</h3>
            </div>
            <p className="text-sm text-texto-secundario">
              Premium se define como profundidad operativa superior (seguimiento y análisis extendido), no solo eliminación de límites.
            </p>
            <div className="text-xs text-texto-terciario space-y-1">
              <p>Estado actual: <span className="text-texto-principal font-semibold">{estadoPlan.activo ? 'Activo' : 'Base'}</span></p>
              <p>Plan: <span className="text-texto-principal font-semibold">{estadoPlan.planId ?? 'N/A'}</span></p>
              <p>Actualizado: <span className="text-texto-principal font-semibold">{estadoPlan.actualizadoEn ?? 'N/A'}</span></p>
            </div>
          </div>
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

          {/* Notificaciones */}
          <div className="tarjeta p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-neon-verde/10 border border-neon-verde/30 flex items-center justify-center">
                <Shield className="w-5 h-5 text-neon-verde" />
              </div>
              <div>
                <h3 className="text-lg font-futurista text-texto-principal">Notificaciones</h3>
                <p className="text-xs text-texto-secundario">
                  Controla alertas por email para partidos, suscripción y resumen semanal.
                </p>
              </div>
            </div>

            {cargandoNotificaciones ? (
              <p className="text-sm text-texto-secundario">Cargando preferencias…</p>
            ) : (
              <div className="space-y-3">
                <label className="flex items-center justify-between gap-3 text-sm text-texto-secundario">
                  <span>Email habilitado</span>
                  <input
                    type="checkbox"
                    className="accent-neon-verde"
                    checked={prefsNotificaciones.email_habilitado}
                    onChange={(event) => actualizarPreferencia('email_habilitado', event.target.checked)}
                  />
                </label>

                <label className="flex items-center justify-between gap-3 text-sm text-texto-secundario">
                  <span>Alertas de partidos</span>
                  <input
                    type="checkbox"
                    className="accent-neon-verde"
                    checked={prefsNotificaciones.alertas_partidos}
                    onChange={(event) => actualizarPreferencia('alertas_partidos', event.target.checked)}
                  />
                </label>

                <label className="flex items-center justify-between gap-3 text-sm text-texto-secundario">
                  <span>Alertas de suscripción</span>
                  <input
                    type="checkbox"
                    className="accent-neon-verde"
                    checked={prefsNotificaciones.alertas_suscripcion}
                    onChange={(event) => actualizarPreferencia('alertas_suscripcion', event.target.checked)}
                  />
                </label>

                <label className="flex items-center justify-between gap-3 text-sm text-texto-secundario">
                  <span>Resumen semanal</span>
                  <input
                    type="checkbox"
                    className="accent-neon-verde"
                    checked={prefsNotificaciones.resumen_semanal}
                    onChange={(event) => actualizarPreferencia('resumen_semanal', event.target.checked)}
                  />
                </label>
              </div>
            )}

            <div className="rounded-lg border border-neon-cyan/20 bg-futurista-oscuro/40 p-3 space-y-2">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs uppercase tracking-wider text-texto-terciario">Entrega 24h</p>
                <span className={`text-xs px-2 py-1 rounded border ${estadoEntrega.color}`}>{estadoEntrega.etiqueta}</span>
              </div>
              <p className="text-sm text-texto-secundario">
                Tasa de entrega:{' '}
                <span className="font-semibold text-texto-principal">
                  {metricasEntrega?.tasa_entrega_pct === null || metricasEntrega?.tasa_entrega_pct === undefined
                    ? 'N/D'
                    : `${metricasEntrega.tasa_entrega_pct.toFixed(1)}%`}
                </span>
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs text-texto-secundario">
                <p>Enviados: {metricasEntrega?.totales.enviados ?? 0}</p>
                <p>Fallidos: {metricasEntrega?.totales.fallidos ?? 0}</p>
                <p>Omitidos: {metricasEntrega?.totales.omitidos ?? 0}</p>
                <p>Reprogramados: {metricasEntrega?.totales.reprogramados ?? 0}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <Boton variante="primario" onClick={() => void guardarNotificaciones()} disabled={guardandoNotificaciones || cargandoNotificaciones}>
                {guardandoNotificaciones ? 'Guardando…' : 'Guardar notificaciones'}
              </Boton>
              <Boton variante="secundario" onClick={() => void probarNotificaciones()} disabled={cargandoNotificaciones}>
                Enviar prueba
              </Boton>
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
