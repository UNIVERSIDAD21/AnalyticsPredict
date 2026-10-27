import { afterEach, expect, it, vi } from 'vitest';
import { clienteAPI } from '../api';
import { obtenerPartidosProximos, obtenerPartido } from './partidos';

afterEach(() => vi.restoreAllMocks());
it('el detalle conserva torneo, temporada, ceros observados y mitades desconocidas', async () => {
  vi.spyOn(clienteAPI, 'get').mockResolvedValue({ data: {
    id: 'p1', competicion_id: 'mls', temporada_id: '2026', local_goles_1t: 0,
    local_goles_2t: null, local_corners_total: 0, local_corners_1t: null,
    local_disparos_arco: null, visitante_goles_total: 0,
  } });
  const p = await obtenerPartido('p1');
  expect(p.competicion).toBe('mls'); expect(p.temporadaId).toBe('2026');
  expect(p.localGoles1t).toBe(0); expect(p.localGoles2t).toBeUndefined();
  expect(p.localCornersTotal).toBe(0); expect(p.localCorners1t).toBeUndefined();
  expect(p.localDisparosArco).toBeUndefined(); expect(p.visitanteGolesTotal).toBe(0);
});
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
