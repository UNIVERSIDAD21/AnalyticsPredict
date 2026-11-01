/**
 * ModalGuardarApuestaFutbol.tsx - Modal minimalista para guardar apuestas de futbol
 */

import { useEffect, useState } from 'react';
import { Boton } from '../atomos';
import { BadgeConfianza } from '../moleculas';
import type { NivelConfianza, TipoMercadoFutbol } from '../../tipos/futbol';
import { ETIQUETAS_MERCADOS } from '../../tipos/futbol';

interface Props {
  mostrar: boolean;
  onCerrar: () => void;
  onGuardar: (stake: number, cuota: number) => void;
  cargando?: boolean;
  partidoInfo: {
    equipoLocal: string;
    equipoVisitante: string;
    fecha: string;
  };
  recomendacion: {
    mercado: TipoMercadoFutbol;
    lado: 'OVER' | 'UNDER';
    linea: number;
    cuota?: number;
    probabilidad: number | null;
    confianza: NivelConfianza | null;
    esRecomendacion: boolean;
  };
}

export function ModalGuardarApuestaFutbol({
  mostrar,
  onCerrar,
  onGuardar,
  cargando,
  partidoInfo,
  recomendacion,
}: Props) {
  const [stake, setStake] = useState('');
  const [cuotaManual, setCuotaManual] = useState('');
  const requiereCuota = !Number.isFinite(recomendacion.cuota) || (recomendacion.cuota ?? 0) <= 1;
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mostrar) {
      setStake('');
      setCuotaManual('');
      setError(null);
    }
  }, [mostrar]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const stakeNum = Number(stake);
    if (!stake || !Number.isFinite(stakeNum) || stakeNum <= 0) {
      setError('Ingresa un monto valido.');
      return;
    }
    const cuota = requiereCuota ? Number(cuotaManual) : recomendacion.cuota!;
    if (!Number.isFinite(cuota) || cuota <= 1) {
      setError('Ingresa la cuota decimal real, mayor que 1.');
      return;
    }
    setError(null);
    onGuardar(stakeNum, cuota);
  };

  if (!mostrar) return null;

  const etiquetaMercado =
    ETIQUETAS_MERCADOS[recomendacion.mercado] ?? recomendacion.mercado;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 overflow-y-auto">
      <div role="dialog" aria-modal="true" aria-labelledby="titulo-guardar-futbol" className="w-full max-w-lg rounded-xl border border-neon-cyan/30 bg-futurista-oscuro p-6">
        <h2 id="titulo-guardar-futbol" className="text-xl font-bold text-texto-principal mb-4">
          Guardar Apuesta
        </h2>

        <div className="space-y-3 mb-6 p-4 bg-futurista-oscuro/30 rounded-lg border border-neon-cyan/10">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <span className="text-texto-terciario">Partido:</span>
            <span className="text-texto-principal font-medium">
              {partidoInfo.equipoLocal} vs {partidoInfo.equipoVisitante}
            </span>

            <span className="text-texto-terciario">Fecha:</span>
            <span className="text-texto-principal">{partidoInfo.fecha}</span>

            <span className="text-texto-terciario">Mercado:</span>
            <span className="text-texto-principal">{etiquetaMercado}</span>

            <span className="text-texto-terciario">Apuesta:</span>
            <span className="text-texto-principal font-bold">
              {recomendacion.lado} {recomendacion.linea}
            </span>

            <span className="text-texto-terciario">Registro:</span>
            <span className="text-texto-principal">
              {recomendacion.esRecomendacion ? 'Recomendación exacta' : 'Selección manual'}
            </span>

            <span className="text-texto-terciario">Cuota:</span>
            <span className="text-texto-principal">
              {recomendacion.cuota != null && recomendacion.cuota > 1
                ? recomendacion.cuota.toFixed(2)
                : 'N/D'}
            </span>

            <span className="text-texto-terciario">Probabilidad:</span>
            <span className="text-texto-principal">
              {recomendacion.probabilidad === null
                ? 'N/D'
                : `${(recomendacion.probabilidad * 100).toFixed(1)}%`}
            </span>

            <span className="text-texto-terciario">Confianza:</span>
            {recomendacion.confianza
              ? <BadgeConfianza nivel={recomendacion.confianza} />
              : <span className="text-texto-principal">N/D</span>}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {requiereCuota && <div className="mb-4">
            <label htmlFor="cuota-manual-futbol" className="block text-sm text-texto-secundario mb-2">Cuota decimal real</label>
            <input id="cuota-manual-futbol" type="number" min="1.01" step="any" required value={cuotaManual}
              onChange={event => setCuotaManual(event.target.value)} className="w-full px-4 py-2 bg-futurista-oscuro border border-neon-cyan/30 rounded-lg text-texto-principal" />
            <p className="mt-1 text-xs text-texto-terciario">Esta competición no aportó una cuota para tu selección. Introduce la que utilizaste; no se inventa una cuota.</p>
          </div>}
          <div className="mb-4">
            <label htmlFor="stake-futbol" className="block text-sm font-medium text-texto-secundario mb-2">
              Monto a Apostar
            </label>
            <input
              id="stake-futbol"
              type="number"
              step="0.01"
              min="0.01"
              value={stake}
              onChange={(event) => setStake(event.target.value)}
              placeholder="Ej: 100.00"
              className="w-full px-4 py-2 bg-futurista-oscuro border border-neon-cyan/30 rounded-lg text-texto-principal focus:border-neon-cyan focus:outline-none"
              required
              autoFocus
            />
            {error && <p className="text-xs text-neon-rojo mt-2">{error}</p>}
          </div>

          <div className="flex gap-3">
            <Boton
              type="button"
              variante="secundario"
              onClick={onCerrar}
              className="flex-1"
            >
              Cancelar
            </Boton>
            <Boton
              type="submit"
              variante="primario"
              cargando={cargando}
              className="flex-1"
            >
              Guardar Apuesta
            </Boton>
          </div>
        </form>
      </div>
    </div>
  );
}
