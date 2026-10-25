"""Probabilidad conjunta WNBA propia; sin penalizaciones/confianza NBA prestadas."""
import json
import math
from types import SimpleNamespace
from uuid import UUID

import numpy as np

from motor.wnba import alcance, exigir
from motor.wnba_ampliado import ajustar_ot, predecir_ampliado
from servicios import predictor_wnba as svc


def es_wnba(s):
    return any(isinstance(r,dict) and r.get('tipo')=='trazabilidad_wnba' for r in (s.get('razones') or []))


def evaluar(selecciones, guardar=False):
    exigir(bool(selecciones) and all(es_wnba(s) for s in selecciones),'No mezclar WNBA con selecciones de otras ligas')
    grupos={};claves=set();producto=1.0
    for s in selecciones:
        exigir(math.isfinite(float(s['cuota'])) and 1 < float(s['cuota']) <= 1000,'Cuota WNBA inválida')
        if guardar:svc.validar_guardado(SimpleNamespace(**s))
        evidencia=next(r for r in s['razones'] if r.get('tipo')=='trazabilidad_wnba')
        aid=str(UUID(evidencia['analisis_id']))
        r=json.loads((svc.journal()/(aid+'.json')).read_text())
        exigir(r['modo'] in ('PREPARTIDO','MANUAL') and r.get('contrato_prediccion')=='wnba-condicional-ot-v2','Combinadas solo PRE WNBA v2')
        exigir(s['equipo_local']==r['equipo_local'] and s['equipo_visitante']==r['equipo_visitante']
               and str(s.get('partido_id'))==str(r['partido_id']) and s['mercado']==r['mercado']
               and float(s['linea'])==r['linea'],'Selección distinta del snapshot WNBA')
        prob=r['probabilidades'][s['lado'].lower()]
        exigir(prob is not None,'Mercado WNBA N/D: no permite evaluar una selección sin probabilidad')
        exigir(abs(float(s['probabilidad_sistema'])-prob)<1e-9,'Probabilidad WNBA alterada')
        key=(r['partido_id'] or (r['equipo_local_id'],r['equipo_visitante_id'],r['corte_exclusivo']))
        clave=(str(key),s['mercado'],s['lado'],s['linea'])
        exigir(clave not in claves,'Selección duplicada en combinada WNBA');claves.add(clave)
        grupos.setdefault(str(key),[]).append((s,r));producto*=prob
    conjunta=1.0;retorno=1.0;detalles=[]
    for key,ls in grupos.items():
        r=ls[0][1]
        exigir(all(x['modelo_version']==r['modelo_version'] for _,x in ls),'Alcances incompatibles del mismo fixture; igualar temporadas/corte')
        m=svc.cargar_publicacion(r['publicacion_version'])
        ts=[t['id'] for t in r['temporadas_solicitadas']]
        rows=alcance(m['datos'],ts,r['corte_exclusivo'],r['fases_solicitadas'])
        model=svc.ajuste_cache(m['version'],m['dataset_sha256'],tuple(sorted(ts)),r['corte_exclusivo'],tuple(sorted(r['fases_solicitadas'])),json.dumps(rows,sort_keys=True,separators=(',',':')))
        proy=predecir_ampliado(model,r['equipo_local_id'],r['equipo_visitante_id'],r['mercado'],r['linea'],[],ajustar_ot(rows),devolver_muestras=True)
        exigir(all(s['mercado'] in proy['_muestras'] for s,_ in ls),'Mercado WNBA N/D en la distribución conjunta')
        wins=np.ones(len(proy['_muestras'][r['mercado']]),bool);pay=np.ones(len(wins))
        for s,_ in ls:
            vals=proy['_muestras'][s['mercado']];line=float(s['linea'])
            win=vals>line if s['lado']=='OVER' else vals<line
            push=vals==line
            wins &= win;pay *= np.where(win,float(s['cuota']),np.where(push,1.,0.))
        pg=float(wins.mean());pr=float(pay.mean());conjunta*=pg;retorno*=pr
        detalles.append({'partido_id':key,'n':len(ls),'probabilidad_conjunta':pg,'retorno_bruto_esperado':pr,'metodo':'Distribución conjunta WNBA Sobol, con devolución push'})
    exigir(producto>0,'Probabilidad conjunta N/D: una selección tiene masa estimada0; no fabricar factor')
    return {'probabilidad_independiente':producto,'probabilidad_ajustada':conjunta,'factor_correlacion':conjunta/producto,
            'valor_esperado_unidad':retorno-1,'n_partidos_unicos':len(grupos),'tiene_mismo_partido':any(len(v)>1 for v in grupos.values()),
            'advertencias':['RAW WNBA sin calibrar; mismas simulaciones por fixture, independencia supuesta entre fixtures distintos. Sin score, Kelly ni recomendación.',
                            'El retorno esperado contempla pushes de cada selección; no es rentabilidad demostrada.'],
            'detalles':detalles}
