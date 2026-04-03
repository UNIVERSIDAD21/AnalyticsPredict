/**
 * CreadorCombinada.tsx — Constructor de apuestas combinadas
 */

import { useMemo, useState } from 'react';
import { Boton, Input } from '../atomos';
import { IndicadorCorrelacion, ResumenCombinada, SelectorSeleccion } from '../moleculas';
import { SeleccionCombinadaInput } from '../../tipos';
import { useCombinadas } from '../../hooks';
import { useToasts } from '../../contextos/Toasts';

interface PropsCreadorCombinada {
  seleccionActual?: SeleccionCombinadaInput | null;
  onCreada?: () => void;
}

const MERCADOS_CUARTOS = new Set(['Q1', 'Q2', 'Q3', 'Q4']);

function calcularCorrelacion(selecciones: SeleccionCombinadaInput[]) {
  const grupos: Record<string, SeleccionCombinadaInput[]> = {};
  selecciones.forEach((seleccion) => {
    const partidoId = seleccion.partido_id || 'sin-partido';
    if (!grupos[partidoId]) grupos[partidoId] = [];
    grupos[partidoId].push(seleccion);
  });

  let factor = 1;
  const advertencias: string[] = [];
  let tieneMismoPartido = false;

  Object.values(grupos).forEach((grupo) => {
    if (grupo.length <= 1) return;
    tieneMismoPartido = true;
    const mercados = grupo.map((s) => s.mercado);
    const lados = new Set(grupo.map((s) => s.lado));
    const tieneCompleto = mercados.includes('COMPLETO');
    const tieneCuartos = mercados.some((mercado) => MERCADOS_CUARTOS.has(mercado));
    const mismoLado = lados.size === 1;

    let factorGrupo = 1;
    if (tieneCompleto && tieneCuartos && mismoLado) {
      factorGrupo = 0.8;
      advertencias.push('⚠️ CORRELACIÓN ALTA: completo + períodos del mismo partido.');
    } else if (tieneCompleto && tieneCuartos && !mismoLado) {
      factorGrupo = 0.93;
      advertencias.push('⚠️ CORRELACIÓN MEDIA: completo + períodos con lados mixtos.');
    } else if (!tieneCompleto && tieneCuartos && mismoLado) {
      factorGrupo = 0.84;
      advertencias.push('⚠️ CORRELACIÓN ALTA: múltiples períodos del mismo partido.');
    } else if (!tieneCompleto && tieneCuartos && !mismoLado) {
      factorGrupo = 0.96;
      advertencias.push('⚠️ CORRELACIÓN BAJA: períodos del mismo partido con lados mixtos.');
    }

    factor *= factorGrupo;
  });

  return { factor, advertencias, tieneMismoPartido };
}

export function CreadorCombinada({ seleccionActual, onCreada }: PropsCreadorCombinada) {
  const [selecciones, setSelecciones] = useState<SeleccionCombinadaInput[]>([]);
  const [stake, setStake] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { crear, estado } = useCombinadas();
  const { agregarToast } = useToasts();

  const cuotaTotal = useMemo(() => {
    if (!selecciones.length) return 1;
    return selecciones.reduce((acc, seleccion) => acc * (seleccion.cuota || 1), 1);
  }, [selecciones]);

  const probabilidadIndependiente = useMemo(() => {
    if (!selecciones.length) return 0;
    return selecciones.reduce((acc, seleccion) => acc * (seleccion.probabilidad_sistema || 0), 1);
  }, [selecciones]);

  const correlacion = useMemo(() => calcularCorrelacion(selecciones), [selecciones]);
  const probabilidadAjustada = probabilidadIndependiente * correlacion.factor;
  const edge = cuotaTotal * probabilidadAjustada - 1;

  const agregarSeleccionActual = () => {
    if (!seleccionActual) return;
    setSelecciones((prev) => [...prev, seleccionActual]);
  };

  const eliminarSeleccion = (indice: number) => {
    setSelecciones((prev) => prev.filter((_, idx) => idx !== indice));
  };

  const guardarCombinada = async () => {
    const stakeNumero = Number(stake);
    if (selecciones.length < 2) {
      setError('Agrega al menos 2 selecciones para crear una combinada.');
      return;
    }
    if (!stake || stakeNumero <= 0) {
      setError('Ingresa un stake válido.');
      return;
    }
    setError(null);
    await crear({
      stake: stakeNumero,
      cuota_total: Number(cuotaTotal.toFixed(2)),
      selecciones,
    });
    agregarToast({
      tipo: 'success',
      titulo: 'Combinada creada',
      mensaje: 'Tu parlay se guardó en la bitácora.',
    });
    setSelecciones([]);
    setStake('');
    onCreada?.();
  };

  return (
    <div className="tarjeta p-5 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h3 className="text-xl font-futurista text-texto-principal">Creador de combinadas</h3>
          <p className="text-sm text-texto-secundario">
            Agrega selecciones y revisa correlaciones antes de guardar.
          </p>
        </div>
        {seleccionActual && (
          <Boton variante="secundario" tamano="sm" onClick={agregarSeleccionActual}>
            Agregar selección actual
          </Boton>
        )}
      </div>

      {selecciones.length === 0 ? (
        <p className="text-sm text-texto-secundario">Sin selecciones en la combinada.</p>
      ) : (
        <div className="space-y-3">
          {selecciones.map((seleccion, indice) => (
            <SelectorSeleccion
              key={`${seleccion.partido_id}-${seleccion.mercado}-${indice}`}
              seleccion={seleccion}
              onEliminar={() => eliminarSeleccion(indice)}
            />
          ))}
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-4">
        <Input
          etiqueta="Stake"
          type="number"
          min="0"
          value={stake}
          onChange={(event) => setStake(event.target.value)}
        />
        <div className="flex items-center">
          <IndicadorCorrelacion
            factor={correlacion.factor}
            tieneCorrelacion={correlacion.tieneMismoPartido}
          />
        </div>
      </div>

      <ResumenCombinada
        cuotaTotal={cuotaTotal}
        probabilidadIndependiente={probabilidadIndependiente}
        probabilidadAjustada={probabilidadAjustada}
        edge={selecciones.length > 0 ? edge : null}
      />

      {correlacion.advertencias.length > 0 && (
        <div className="text-xs text-advertencia-500 space-y-1">
          {correlacion.advertencias.map((advertencia) => (
            <p key={advertencia}>{advertencia}</p>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-neon-rojo">{error}</p>}

      <Boton
        variante="primario"
        onClick={guardarCombinada}
        disabled={estado === 'cargando'}
      >
        {estado === 'cargando' ? 'Guardando...' : 'Guardar combinada'}
      </Boton>
    </div>
  );
}
