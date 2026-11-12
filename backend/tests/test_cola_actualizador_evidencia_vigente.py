"""Una deuda de campo resuelta no revive por rechazos posteriores de otro origen."""
from datetime import datetime,timezone
from types import SimpleNamespace
import pytest
from servicios import flujo_cola_actualizador as flow
from servicios.actualizador_partidos import OBJETIVOS

@pytest.mark.parametrize('valor,acreditado,queda_pendiente',[(5,True,False),(0,True,False),(5,False,True),(None,True,True)])
def test_rechazo_nuevo_respeta_soporte_vigente_sin_ocultar_null(monkeypatch,valor,acreditado,queda_pendiente):
    pendientes=[]
    monkeypatch.setattr(flow.cola,'lote',lambda conn,run,etapa,insumo,ahora,callback:('lote',callback('lote'),True))
    monkeypatch.setattr(flow.cola,'guardar_pendiente',lambda conn,item,lote:pendientes.append(item.clave[-1]))
    monkeypatch.setattr(flow,'campo_con_observacion_vigente',lambda conn,pid,campo,v:v is not None and acreditado)
    field='local_corners_total'
    row={k:None for k in OBJETIVOS}
    row.update(id='2aa5bb45-52bc-4a55-8df8-c36eaab7dc97',liga='esp.copa_del_rey',id_fuente='401928493',fecha_partido=datetime(2026,10,27,tzinfo=timezone.utc))
    row[field]=valor
    flow.confirmar_estadisticas(None,'run',row,{'header':{'season':{'year':2026}}},
        {'sha256':'a'*64,'observado_en':'2026-11-08T16:00:00+00:00'},SimpleNamespace(actualizaciones={}),{},
        [{'campo':field,'motivo':'BLOQUE_CEROS_SIN_COBERTURA'}],datetime(2026,11,8,16,tzinfo=timezone.utc))
    assert (field in pendientes) is queda_pendiente
    assert len(pendientes)==(6 if queda_pendiente else 5)
