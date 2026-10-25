#!/usr/bin/env python3
"""Evaluación temporal v2 según protocolo publicado antes de medir. Sin BD/DML.

Reproduce candidato v1 guardado; añade OT TRAIN y condicionamiento WNBA. No activa,
calibra ni asigna los resultados al serving de otras temporadas o al refit.
"""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from motor.wnba import conocido, covarianza, huella, MERCADOS
from motor.wnba_ampliado import ajustar_ot, predecir_ampliado, VERSION
from servicios.predictor_wnba import cargar, escribir


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--salida',type=Path,required=True)
    a=p.parse_args();a.salida.mkdir(mode=0o700,parents=True,exist_ok=True)
    assert not (a.salida/'evaluacion.json').exists(),'No sobrescribir evidencia'
    publicado=cargar();datos=[r for r in publicado['datos'] if r['fase']=='REG']
    train=[r for r in datos if r['fecha']<'2024-01-01']
    cal=[r for r in datos if '2024-07-15'<=r['fecha']<'2025-01-01']
    test=[r for r in datos if r['fecha']>='2025-01-01']
    ridge=publicado['validacion']['candidato']
    cal=[r for r in cal if conocido(ridge,r)]
    media=np.array([r['y'] for r in train]).mean(axis=0)
    coef=np.zeros_like(ridge['coeficientes']);coef[0]=media[4:];coef[1]=media[:4]-media[4:]
    base={**ridge,'coeficientes':coef.tolist(),'covarianza':covarianza(np.array([r['y'] for r in cal])-media).tolist()}
    ot=ajustar_ot(train)
    lineas={k:[math.floor(float(media[ix].sum()))+.5,round(float(media[ix].sum()))] for k,ix in MERCADOS.items()}
    candidato={'algoritmo':VERSION,'ridge':ridge,'referencia':base,'ot_train':ot,'lineas_train':lineas,
               'publicacion_origen':publicado['version'],'dataset_sha256':publicado['dataset_sha256'],
               'protocolo':'PROTOCOLO_WNBA_PARIDAD_2026-10-25.md','calibracion':'SIN_CALIBRAR','sobol_muestras':32768}
    candidato['version']='wnba-v2-candidato-'+huella(candidato)[:24]
    escribir(a.salida/'candidato.json',candidato)
    cohors=[];rechazados=[];metrics={}
    for n,r in enumerate(test):
        if not conocido(ridge,r):rechazados.append({'id':r['id'],'motivo':'Muestra/equipo no soportado en TRAIN'});continue
        for corte in range(4):
            parciales=[[r['y'][i],r['y'][i+4]] for i in range(corte)]
            try:
                v=predecir_ampliado(ridge,r['local_id'],r['visitante_id'],'COMPLETO',lineas['COMPLETO'][0],parciales,ot,lineas=lineas)
                b=predecir_ampliado(base,r['local_id'],r['visitante_id'],'COMPLETO',lineas['COMPLETO'][0],parciales,ot,lineas=lineas)
            except ValueError as e:
                rechazados.append({'id':r['id'],'corte':corte,'motivo':str(e)});continue
            row={'id':r['id'],'fecha':r['fecha'],'corte':corte,'modelo':v,'referencia':b,'observados':{}}
            for k,ix in MERCADOS.items():
                if k!='COMPLETO' and int(k[1])<=corte:continue
                y=(r['local_total']+r['visitante_total']) if k=='COMPLETO' and corte==0 else sum(r['y'][i] for i in ix)
                row['observados'][k]=y
                key=f'{corte}:{k}';m=metrics.setdefault(key,{'modelo':[],'referencia':[]})
                for nombre,proy in [('modelo',v),('referencia',b)]:
                    pr=proy['predicciones'][k];line=lineas[k][0];ps=proy['evaluacion_lineas'][k][str(line)]
                    target=[float(y>line),float(y<line),float(y==line)]
                    prob=np.array(list(ps.values()));integer=lineas[k][1];pp=proy['evaluacion_lineas'][k][str(integer)]
                    ti=np.array([float(y>integer),float(y<integer),float(y==integer)])
                    m[nombre].append({'mae':abs(pr['media_total']-y),'brier':float(((prob-target)**2).sum()),
                       'brier_entera':float(((np.array(list(pp.values()))-ti)**2).sum()),
                       'logloss':float(-np.log(max(float(prob@target),1e-12))),
                       'cobertura80':float(pr['intervalo_80_raw'][0]<=y<=pr['intervalo_80_raw'][1])})
            cohors.append(row)
        if n%100==0:print('EVAL procesados',n,'de',len(test),flush=True)
    resumen={k:{nombre:{'n':len(vals),**{met:float(np.mean([x[met] for x in vals])) for met in vals[0]}} for nombre,vals in ms.items()} for k,ms in metrics.items()}
    reporte={'candidato':candidato['version'],'train_n':len(train),'cal_dispersion_n':len(cal),'ot_train_n':ot['n'],
             'eval_denominador':len(test),'predicciones_por_corte':{str(q):sum(r['corte']==q for r in cohors) for q in range(4)},
             'metricas':resumen,'abstenciones':rechazados,'cohorte_sha256':huella(cohors),
             'limites':'Retrospectiva sobre datos ya observados; sin calibración, prospectiva, selección EVAL ni eficacia acreditada del refit por alcance. OT y cortes v2 no heredan las métricas v1.'}
    escribir(a.salida/'cohorte.json',cohors);escribir(a.salida/'evaluacion.json',reporte)
    print(json.dumps({k:v for k,v in reporte.items() if k not in ('abstenciones','metricas')}),flush=True)

if __name__=='__main__':main()
