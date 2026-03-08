import { clienteAPI, extraerMensajeError } from './api';
import { ContratoExplicacion } from '../tipos/explicabilidad';

const EXPLICABILIDAD_ENABLED =
  (import.meta.env.VITE_EXPLICABILIDAD_ENABLED ?? 'true').toString().toLowerCase() === 'true';

/**
 * Obtiene explicación canónica v1 de una predicción.
 * Si el feature flag está deshabilitado, retorna null sin llamar API.
 */
export async function obtenerExplicacion(
  predictionId: string
): Promise<ContratoExplicacion | null> {
  if (!EXPLICABILIDAD_ENABLED) {
    return null;
  }

  try {
    const resp = await clienteAPI.get<ContratoExplicacion>(
      `/api/prediccion/${predictionId}/explicacion`,
      { params: { version: 'v1' } }
    );
    return resp.data;
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
