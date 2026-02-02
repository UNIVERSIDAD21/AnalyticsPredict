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
  onGuardar: (stake: number) => void;
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
    probabilidad: number;
    confianza: NivelConfianza;
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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mostrar) {
      setStake('');
      setError(null);
    }
  }, [mostrar]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const stakeNum = Number(stake);
    if (!stake || Number.isNaN(stakeNum) || stakeNum <= 0) {
      setError('Ingresa un monto valido.');
      return;
    }
    setError(null);
    onGuardar(stakeNum);
  };

  if (!mostrar) return null;

  const etiquetaMercado =
    ETIQUETAS_MERCADOS[recomendacion.mercado] ?? recomendacion.mercado;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 overflow-y-auto">
      <div className="w-full max-w-lg rounded-xl border border-neon-cyan/30 bg-futurista-oscuro p-6">
        <h2 className="text-xl font-bold text-texto-principal mb-4">
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

            {recomendacion.cuota !== undefined && (
              <>
                <span className="text-texto-terciario">Cuota:</span>
                <span className="text-texto-principal">
                  {recomendacion.cuota.toFixed(2)}
                </span>
              </>
            )}

            <span className="text-texto-terciario">Probabilidad:</span>
            <span className="text-texto-principal">
              {(recomendacion.probabilidad * 100).toFixed(1)}%
            </span>

            <span className="text-texto-terciario">Confianza:</span>
            <BadgeConfianza nivel={recomendacion.confianza} />
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-texto-secundario mb-2">
              Monto a Apostar
            </label>
            <input
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
