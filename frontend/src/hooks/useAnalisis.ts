// hace parte del diseño de analisis
/**
 * useAnalisis.ts — Hook para manejar análisis de partidos
 *
 * Fase 2: Ahora incluye advertencias del backend para mostrar en UI.
 */

import { useState, useCallback } from 'react';
import { PeticionAnalisis, ResultadoAnalisis, EstadoPeticion } from '../tipos';
import { analizarPartido } from '../servicios';
import { useConfiguracionUsuario } from '../contextos/ConfiguracionUsuario';
import { useToasts } from '../contextos/Toasts';

interface RetornoUseAnalisis {
  /** Resultado del análisis */
  resultado: ResultadoAnalisis | null;

  /** Advertencias del backend (Fase 2) */
  advertencias: string[];

  /** Estado de la petición */
  estado: EstadoPeticion;

  /** Mensaje de error si hay */
  error: string | null;

  /** Ejecutar análisis */
  analizar: (peticion: PeticionAnalisis) => Promise<void>;

  /** Limpiar estado */
  limpiar: () => void;
}

/**
 * Hook que gestiona el análisis de partidos.
 * Fase 2: Ahora retorna advertencias del backend para mostrar en UI.
 */
export function useAnalisis(): RetornoUseAnalisis {
  const [resultado, setResultado] = useState<ResultadoAnalisis | null>(null);
  const [advertencias, setAdvertencias] = useState<string[]>([]);
  const [estado, setEstado] = useState<EstadoPeticion>('inactivo');
  const [error, setError] = useState<string | null>(null);
  const { configuracion } = useConfiguracionUsuario();
  const { agregarToast } = useToasts();

  const analizar = useCallback(async (peticion: PeticionAnalisis) => {
    setEstado('cargando');
    setError(null);
    setResultado(null);
    setAdvertencias([]);

    try {
      const tieneOver = peticion.cuota_over !== undefined && peticion.cuota_over !== null;
      const tieneUnder = peticion.cuota_under !== undefined && peticion.cuota_under !== null;
      const tieneAmbas = tieneOver && tieneUnder;
      const soloUnaCuota = (tieneOver || tieneUnder) && !tieneAmbas;

      if (configuracion.modoDevig === 'estricto' && soloUnaCuota) {
        const mensaje =
          'Modo de-vig estricto requiere cuotas OVER y UNDER. Completa ambas cuotas o cambia a estimado.';
        setError(mensaje);
        setEstado('error');
        return;
      }

      let modoDevigFinal = peticion.modo_devig;
      const advertenciasLocales: string[] = [];

      if (tieneAmbas) {
        modoDevigFinal = 'estricto';
      } else if (soloUnaCuota && configuracion.modoDevig === 'estimado') {
        modoDevigFinal = 'estimado';
        advertenciasLocales.push('DEVIG_ESTIMADO_PENALIZA');
      }

      if (modoDevigFinal === 'estimado') {
        agregarToast({
          titulo: 'De-vig estimado',
          mensaje: 'Solo hay una cuota disponible, se aplica penalización.',
          tipo: 'warning',
        });
      }

      const respuesta = await analizarPartido(
        {
          ...peticion,
          modo_devig: modoDevigFinal,
        },
        configuracion
      );
      setResultado(respuesta.datos);
      setAdvertencias([...advertenciasLocales, ...respuesta.advertencias]);
      setEstado('exito');
    } catch (err) {
      const mensaje = err instanceof Error ? err.message : 'Error al analizar partido';
      setError(mensaje);
      setEstado('error');
    }
  }, [agregarToast, configuracion]);

  const limpiar = useCallback(() => {
    setResultado(null);
    setAdvertencias([]);
    setEstado('inactivo');
    setError(null);
  }, []);

  return {
    resultado,
    advertencias,
    estado,
    error,
    analizar,
    limpiar,
  };
}
