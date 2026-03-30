import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Compass, Rocket, ShieldCheck } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton } from '../atomos';
import { useAuth } from '../../contextos/AuthContext';
import {
  guardarEstadoOnboarding,
  registrarEventoOnboarding,
  type PerfilOnboarding,
} from '../../servicios/onboarding';
import { registrarEventoProducto } from '../../servicios/productAnalytics';
import { useToasts } from '../../contextos/Toasts';


export function PaginaOnboarding() {
  const { usuario } = useAuth();
  const { agregarToast } = useToasts();
  const navigate = useNavigate();
  const location = useLocation();

  const destinoPostOnboarding = ((location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/dashboard');

  const [paso, setPaso] = useState(1);
  const [perfil, setPerfil] = useState<PerfilOnboarding>({
    nombre: '',
    objetivoPrincipal: 'rentabilidad',
    deportePreferido: 'ambos',
    frecuencia: 'semanal',
    bankrollReferencial: null,
  });

  const puedeAvanzar = useMemo(() => {
    if (paso === 1) return perfil.nombre.trim().length >= 2;
    if (paso === 2) return true;
    return true;
  }, [paso, perfil.nombre]);

  useEffect(() => {
    const payload = { paso_inicial: 1, destino: destinoPostOnboarding };
    void registrarEventoOnboarding('onboarding_started', payload);
    registrarEventoProducto('onboarding_started', payload);
  }, [destinoPostOnboarding]);

  const finalizar = async () => {
    if (!usuario?.id) return;

    await guardarEstadoOnboarding(String(usuario.id), perfil);
    const payloadFin = { objetivo: perfil.objetivoPrincipal, destino: destinoPostOnboarding };
    await registrarEventoOnboarding('onboarding_completed', payloadFin);
    registrarEventoProducto('onboarding_completed', payloadFin);

    agregarToast({
      titulo: 'Onboarding completado',
      mensaje: 'Tu perfil base quedó activo y ya puedes operar sin fricción.',
      tipo: 'success',
    });
    navigate(destinoPostOnboarding, { replace: true });
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 max-w-4xl w-full">
        <div className="tarjeta p-6 lg:p-8 space-y-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-futurista text-texto-principal">Onboarding inicial</h2>
              <p className="text-sm text-texto-secundario">
                Configura tu perfil base para priorizar métricas y recomendaciones.
              </p>
            </div>
            <span className="text-xs uppercase tracking-wider text-texto-terciario">Paso {paso}/3</span>
          </div>

          <div className="h-2 rounded-full bg-futurista-oscuro/80 border border-neon-cyan/20 overflow-hidden">
            <div className="h-full bg-neon-cyan" style={{ width: `${(paso / 3) * 100}%` }} />
          </div>

          {destinoPostOnboarding !== '/dashboard' && (
            <div className="rounded-lg border border-neon-cyan/20 bg-futurista-oscuro/40 p-3 text-sm text-texto-secundario">
              Terminando este onboarding te llevamos directo a <strong className="text-texto-principal">{destinoPostOnboarding}</strong> para continuar donde te quedaste.
            </div>
          )}

          {paso === 1 && (
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <Compass className="w-5 h-5 text-neon-cyan" />
                <h3 className="text-lg font-semibold text-texto-principal">Perfil base</h3>
              </div>

              <div>
                <label className="text-xs uppercase tracking-widest text-texto-secundario">¿Cómo quieres que te llamemos?</label>
                <input
                  value={perfil.nombre}
                  onChange={(event) => setPerfil((prev) => ({ ...prev, nombre: event.target.value }))}
                  className="mt-2 w-full rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal focus:outline-none focus:border-neon-cyan"
                  placeholder="Ej: Erik"
                />
              </div>

              <div>
                <label className="text-xs uppercase tracking-widest text-texto-secundario">Frecuencia de uso esperada</label>
                <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {(['diaria', 'semanal', 'ocasional'] as const).map((opcion) => (
                    <button
                      key={opcion}
                      type="button"
                      className={`px-3 py-2 rounded-lg border text-xs uppercase tracking-wider ${
                        perfil.frecuencia === opcion
                          ? 'border-neon-cyan bg-neon-cyan/10 text-neon-cyan'
                          : 'border-neon-cyan/20 text-texto-secundario'
                      }`}
                      onClick={() => setPerfil((prev) => ({ ...prev, frecuencia: opcion }))}
                    >
                      {opcion}
                    </button>
                  ))}
                </div>
              </div>
            </section>
          )}

          {paso === 2 && (
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <Rocket className="w-5 h-5 text-neon-verde" />
                <h3 className="text-lg font-semibold text-texto-principal">Objetivo principal</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[
                  { id: 'rentabilidad', titulo: 'Rentabilidad' },
                  { id: 'disciplina', titulo: 'Disciplina' },
                  { id: 'aprendizaje', titulo: 'Aprendizaje' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setPerfil((prev) => ({ ...prev, objetivoPrincipal: item.id as PerfilOnboarding['objetivoPrincipal'] }))}
                    className={`p-4 rounded-lg border text-left ${
                      perfil.objetivoPrincipal === item.id
                        ? 'border-neon-verde bg-neon-verde/10 text-neon-verde'
                        : 'border-neon-verde/20 text-texto-secundario'
                    }`}
                  >
                    <p className="font-semibold">{item.titulo}</p>
                  </button>
                ))}
              </div>

              <div>
                <label className="text-xs uppercase tracking-widest text-texto-secundario">Deporte preferido</label>
                <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {(['baloncesto', 'futbol', 'ambos'] as const).map((opcion) => (
                    <button
                      key={opcion}
                      type="button"
                      className={`px-3 py-2 rounded-lg border text-xs uppercase tracking-wider ${
                        perfil.deportePreferido === opcion
                          ? 'border-neon-magenta bg-neon-magenta/10 text-neon-magenta'
                          : 'border-neon-magenta/20 text-texto-secundario'
                      }`}
                      onClick={() => setPerfil((prev) => ({ ...prev, deportePreferido: opcion }))}
                    >
                      {opcion}
                    </button>
                  ))}
                </div>
              </div>
            </section>
          )}

          {paso === 3 && (
            <section className="space-y-4">
              <div className="flex items-center gap-3">
                <ShieldCheck className="w-5 h-5 text-neon-cyan" />
                <h3 className="text-lg font-semibold text-texto-principal">Control de riesgo inicial</h3>
              </div>

              <div>
                <label className="text-xs uppercase tracking-widest text-texto-secundario">Bankroll referencial (opcional)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={perfil.bankrollReferencial ?? ''}
                  onChange={(event) => {
                    const value = event.target.value.trim();
                    setPerfil((prev) => ({ ...prev, bankrollReferencial: value ? Number(value) : null }));
                  }}
                  className="mt-2 w-full rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal focus:outline-none focus:border-neon-cyan"
                  placeholder="Ej: 500"
                />
                <p className="mt-2 text-xs text-texto-terciario">
                  Este valor se usa para personalizar recomendaciones iniciales. Luego puedes ajustarlo en Configuración.
                </p>
              </div>

              <div className="rounded-lg border border-neon-cyan/20 bg-futurista-oscuro/40 p-3 text-sm text-texto-secundario">
                <p><strong>Resumen:</strong> {perfil.nombre || 'Usuario'} · {perfil.objetivoPrincipal} · {perfil.deportePreferido}</p>
              </div>
            </section>
          )}

          <div className="flex items-center justify-between gap-3 pt-2">
            <Boton variante="secundario" onClick={() => setPaso((prev) => Math.max(1, prev - 1))} disabled={paso === 1}>
              Atrás
            </Boton>

            {paso < 3 ? (
              <Boton variante="primario" onClick={() => setPaso((prev) => Math.min(3, prev + 1))} disabled={!puedeAvanzar}>
                Continuar
              </Boton>
            ) : (
              <Boton variante="primario" onClick={finalizar}>
                Ir al dashboard
              </Boton>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
