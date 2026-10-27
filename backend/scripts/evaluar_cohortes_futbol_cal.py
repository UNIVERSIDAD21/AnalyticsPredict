#!/usr/bin/env python3
"""Calibración candidata sobre cohortes causales previamente archivadas.

No regenera emisiones ni convierte TEST ya observado en prospectiva.
Reutiliza el evaluador multiclase (Brier suma de clases = 2× Brier binario).
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluar_agendas_temporal import calibrar,temperatura,metricas,bootstrap,guardar


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cohortes',type=Path,required=True);p.add_argument('--salida',type=Path,required=True)
    a=p.parse_args();a.salida.mkdir(mode=0o700,parents=True,exist_ok=False)
    for f in sorted(a.cohortes.glob('*_PREDICCIONES.jsonl.gz')):
        code=f.name.split('_PREDICCIONES')[0];sha=hashlib.sha256(f.read_bytes()).hexdigest()
        with gzip.open(f,'rt') as src:rows=[json.loads(x) for x in src]
        dates=sorted({r['corte_exclusivo'] for r in rows});mid=dates[len(dates)//2] if dates else None
        buckets=defaultdict(lambda:{'CAL':[],'TEST':[]});rejected=defaultdict(int)
        for r in rows:
            if not all(r.get(k) is not None for k in ('p','p_referencia','media','media_referencia','y','std')):
                rejected[r.get('mercado')]+=1;continue
            block='CAL' if r['corte_exclusivo']<mid else 'TEST'
            val=r['y'];line=r['linea'];prob=r['p'];base=r['p_referencia'];sd=r['std']
            buckets[r['mercado']][block].append({'id':r['partido_id'],'fecha':r['corte_exclusivo'][:10],
                'entera':float(line).is_integer(),'valor':val,'mu':r['media'],'base_mu':r['media_referencia'],
                'y':[int(val>line),int(val<line),int(val==line)],'raw':[prob,1-prob,0],
                'base':[base,1-base,0],'intervalo80':abs(val-r['media'])<=1.2815515655*sd})
        report={'liga':code,'origen':str(f),'sha256_original':sha,'cal_test_frontera':mid,
            'naturaleza':'Reutilización retrospectiva de datos ya observados, no TEST inédito ni prospectiva',
            'publicado':False,'prospectiva_n':0,'resultados':{},'abstenciones':dict(rejected)}
        for key,bs in buckets.items():
            t,reason=calibrar(bs['CAL']);test=bs['TEST']
            for r in test:r['calibrado']=temperatura(r['raw'],t).tolist() if t is not None else r['raw']
            if not test:continue
            ms={k:metricas(test,k) for k in ('raw','base','calibrado')};ci=bootstrap(test,'calibrado','raw') if t else None
            report['resultados'][key]={'cal_n':len(bs['CAL']),'test_n':len(test),'temperatura':t,
                'metricas':ms,'ic95_delta_brier_vs_raw':ci,'publicar':False,
                'bloqueos':[reason] if reason else []}
            report['resultados'][key]['bloqueos']+=['Prospectiva independiente0/200; no transferir a refit/otras ligas/modos']
        if hashlib.sha256(f.read_bytes()).hexdigest()!=sha:raise ValueError('Cohorte original cambió')
        guardar(a.salida/(code+'_metricas.json'),report)
        print(code,'grupos',len(report['resultados']),'original intacto',flush=True)


if __name__=='__main__':main()
