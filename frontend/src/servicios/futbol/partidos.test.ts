import { afterEach, expect, it, vi } from 'vitest';
import { clienteAPI } from '../api';
import { obtenerPartidosProximos } from './partidos';

afterEach(() => vi.restoreAllMocks());
it('usa la paginación real, distingue IDs de nombres y conserva marcadores ausentes', async () => {
  const get = vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: { exito: true, partidos: [{
    id: 'partido', competicion_id: 'liga-id', competicion: 'Liga',
    equipo_local_id: 'local-id', equipo_local: 'Nombre local',
    equipo_visitante_id: 'visitante-id', equipo_visitante: 'Nombre visitante',
    fecha_partido: '2026-10-20T20:00:00Z', goles_local: null, goles_visitante: null,
  }] } });
  const [partido] = await obtenerPartidosProximos({ dias: 7, limite: 100 });
  expect(get).toHaveBeenCalledWith('/api/futbol/partidos/proximos', { params: { dias: 7, tamano: 100 } });
  expect(partido.equipoLocal).toBe('local-id');
  expect(partido.equipoLocalNombre).toBe('Nombre local');
  expect(partido.equipoVisitante).toBe('visitante-id');
  expect(partido.competicion).toBe('liga-id');
  expect(partido.golesLocal).toBeUndefined();
  expect(partido.golesVisitante).toBeUndefined();
});
