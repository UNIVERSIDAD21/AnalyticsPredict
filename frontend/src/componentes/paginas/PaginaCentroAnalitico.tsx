import { useEffect, useMemo, useState } from 'react';
import { Activity, CheckCircle2, Clock3, Layers3, ShieldAlert, Target } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton, Tarjeta } from '../atomos';
import { SelectorDeporte } from '../atomos/SelectorDeporte';
import { useDeporte } from '../../contextos/DeporteContext';
import { listarApuestasAnalizadas } from '../../servicios/bitacora';
import type { ApuestaAnalizada } from '../../tipos/bitacora';

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

type EstadoMadurez = 'MADURO' | 'BETA_LAB';

interface KPIBase {
  apuestasTotales: number;
  resueltas: number;
  ganadas: number;
  winRate: number;
}

function calcularKpis(items: ApuestaAnalizada[]): KPIBase {
  const totales = items.length;
  const resueltas = items.filter((i) => i.estado?.toUpperCase() === 'RESUELTA');
  const ganadas = resueltas.filter((i) => i.resultado_outcome === 'GANADA').length;
  const winRate = resueltas.length > 0 ? (ganadas / resueltas.length) * 100 : 0;
  return { apuestasTotales: totales, resueltas: resueltas.length, ganadas, winRate };
}

export function PaginaCentroAnalitico() {
  const { deporteActivo, esNBA, esFutbol } = useDeporte();
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kpisNBA, setKpisNBA] = useState<KPIBase>({ apuestasTotales: 0, resueltas: 0, ganadas: 0, winRate: 0 });
  const [kpisFutbol, setKpisFutbol] = useState<KPIBase>({ apuestasTotales: 0, resueltas: 0, ganadas: 0, winRate: 0 });

  useEffect(() => {
    const cargar = async () => {
      try {
        setCargando(true);
        setError(null);
        const data = await listarApuestasAnalizadas({ page_size: 500 });
        const items = data.items || [];
        setKpisNBA(calcularKpis(items.filter((i) => i.deporte === 'baloncesto')));
        setKpisFutbol(calcularKpis(items.filter((i) => i.deporte === 'futbol')));
      } catch (e) {
        setError(e instanceof Error ? e.message : 'No se pudieron cargar métricas base.');
      } finally {
        setCargando(false);
      }
    };

    void cargar();
  }, []);

  const kpisActivos = useMemo(() => (esFutbol ? kpisFutbol : kpisNBA), [esFutbol, kpisFutbol, kpisNBA]);

  const estadoMadurez: EstadoMadurez = esNBA ? 'MADURO' : 'BETA_LAB';
  const descripcionMadurez = esNBA
    ? 'NBA es frente comercial principal y módulo más maduro.'
    : 'Fútbol sigue en beta/laboratorio: operativo, pero sin paridad comercial con NBA.';

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <section className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-futurista text-texto-principal flex items-center gap-2">
              <Layers3 className="w-5 h-5 text-neon-cyan" />
              Centro Analítico Multideporte
            </h2>
            <p className="text-sm text-texto-secundario">
              Shell unificado con KPIs base compartidos y madurez visible por deporte.
            </p>
          </div>
          <SelectorDeporte tamaño="md" />
        </section>

        {error && (
          <Tarjeta className="border border-neon-rojo/40 text-neon-rojo p-4">
            {error}
          </Tarjeta>
        )}

        <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Tarjeta className="p-4">
            <p className="text-xs uppercase tracking-wider text-texto-terciario">Apuestas totales</p>
            <p className="text-3xl font-semibold text-texto-principal mt-1">
              {cargando ? '…' : kpisActivos.apuestasTotales}
            </p>
          </Tarjeta>
          <Tarjeta className="p-4">
            <p className="text-xs uppercase tracking-wider text-texto-terciario">Resueltas</p>
            <p className="text-3xl font-semibold text-texto-principal mt-1">
              {cargando ? '…' : kpisActivos.resueltas}
            </p>
          </Tarjeta>
          <Tarjeta className="p-4">
            <p className="text-xs uppercase tracking-wider text-texto-terciario">Ganadas</p>
            <p className="text-3xl font-semibold text-texto-principal mt-1">
              {cargando ? '…' : kpisActivos.ganadas}
            </p>
          </Tarjeta>
          <Tarjeta className="p-4">
            <p className="text-xs uppercase tracking-wider text-texto-terciario">Win rate</p>
            <p className="text-3xl font-semibold text-texto-principal mt-1">
              {cargando ? '…' : `${kpisActivos.winRate.toFixed(1)}%`}
            </p>
          </Tarjeta>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Tarjeta className="p-5 space-y-3 border border-neon-cyan/25">
            <div className="flex items-center gap-2 text-neon-cyan">
              <ShieldAlert className="w-4 h-4" />
              <p className="text-xs uppercase tracking-wider">Madurez visible por deporte</p>
            </div>
            <div className="flex items-center gap-2">
              {estadoMadurez === 'MADURO' ? (
                <CheckCircle2 className="w-5 h-5 text-neon-verde" />
              ) : (
                <Clock3 className="w-5 h-5 text-neon-amarillo" />
              )}
              <p className="text-lg font-semibold text-texto-principal">
                {esNBA ? 'NBA: MADURO' : 'Fútbol: BETA / LAB'}
              </p>
            </div>
            <p className="text-sm text-texto-secundario">{descripcionMadurez}</p>
          </Tarjeta>

          <Tarjeta className="p-5 space-y-3 border border-neon-cyan/25">
            <div className="flex items-center gap-2 text-neon-magenta">
              <Activity className="w-4 h-4" />
              <p className="text-xs uppercase tracking-wider">Navegación común con paneles específicos</p>
            </div>
            <p className="text-sm text-texto-secundario">
              El centro unifica entrada y métricas base. El análisis profundo permanece por dominio para evitar mezclar lógicas incompatibles.
            </p>
            <div className="flex flex-wrap gap-2">
              <Boton variante="secundario" onClick={() => navegar(esNBA ? '/' : '/futbol')}>
                Ir a análisis específico
              </Boton>
              <Boton variante="primario" onClick={() => navegar(esNBA ? '/bitacora' : '/futbol/bitacora')}>
                Ir a bitácora específica
              </Boton>
            </div>
          </Tarjeta>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Tarjeta className="p-5 space-y-3">
            <div className="flex items-center gap-2 text-neon-cyan">
              <Target className="w-4 h-4" />
              <h3 className="text-sm uppercase tracking-wider">Qué comparten NBA y fútbol</h3>
            </div>
            <ul className="text-sm text-texto-secundario space-y-1">
              <li>• Ciclo de apuesta analizada y resolución.</li>
              <li>• KPIs base (totales, resueltas, ganadas, win rate).</li>
              <li>• Trazabilidad operativa y navegación común.</li>
            </ul>
          </Tarjeta>

          <Tarjeta className="p-5 space-y-3">
            <div className="flex items-center gap-2 text-neon-verde">
              <Layers3 className="w-4 h-4" />
              <h3 className="text-sm uppercase tracking-wider">Qué se mantiene específico por deporte</h3>
            </div>
            <ul className="text-sm text-texto-secundario space-y-1">
              <li>• Modelos/mercados/semántica analítica.</li>
              <li>• Tableros y flujos profundos de análisis.</li>
              <li>• Señal comercial y madurez operacional actual.</li>
            </ul>
          </Tarjeta>
        </section>
      </main>
    </div>
  );
}
