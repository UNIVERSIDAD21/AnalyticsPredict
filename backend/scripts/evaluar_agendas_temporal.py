#!/usr/bin/env python3
"""Evaluación offline de candidatos por liga. No importa servicios de serving/BD.

Nunca activa el candidato ni atribuye sus métricas a un refit. Protocolo y
snapshot explícitos, persistidos antes de medir. TEST retrospectivo ya observado.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from scipy.optimize import minimize_scalar
from motor import euroliga as euro, wnba
from motor.wnba_ampliado import condicionar
from motor_autoentrenamiento.entrenador_bd import construir_matriz_diseno, ajustar_ridge, ALPHA_RIDGE, normalizar_nombre


def guardar(p,v):
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else str(x)))


def temperatura(p,t):
    p=np.array(p,float);mask=p>0
    z=np.zeros_like(p);z[mask]=p[mask]**(1/t)
    return z/z.sum(axis=-1,keepdims=True)


def calibrar(rows):
    if len(rows)<200:return None,'CAL-calibrador <200 partidos'
    ys=np.array([r['y'] for r in rows]);counts=ys.sum(axis=0)
    if min(counts[:2])<20 or (rows[0]['entera'] and counts[2]<10):
        return None,'CAL sin 20 casos por lado o 10 pushes en línea entera'
    ps=np.array([r['raw'] for r in rows])
    def loss(t):return float(-(ys*np.log(np.clip(temperatura(ps,t),1e-12,1))).sum(axis=1).mean())
    t=minimize_scalar(loss,bounds=(.5,2),method='bounded',options={'xatol':1e-8})
    return float(t.x),None


def metricas(rows,key):
    p=np.array([r[key] for r in rows]);y=np.array([r['y'] for r in rows])
    if not len(rows):return None
    bins=[]
    for lo in np.arange(0,1,.1):
        ix=(p[:,0]>=lo)&(p[:,0]<(lo+.1+1e-12 if lo>.89 else lo+.1))
        bins.append({'desde':round(float(lo),1),'hasta':round(float(lo+.1),1),'n':int(ix.sum()),
            'probabilidad_media':float(p[ix,0].mean()) if ix.any() else None,
            'frecuencia_over':float(y[ix,0].mean()) if ix.any() else None})
    return {'n':len(rows),'brier':float(((p-y)**2).sum(axis=1).mean()),
        'logloss':float(-(y*np.log(np.clip(p,1e-12,1))).sum(axis=1).mean()),
        'mae':float(np.mean([abs(r['mu' if key!='base' else 'base_mu']-r['valor']) for r in rows])),
        'push_observado':float(y[:,2].mean()),'push_estimado':float(p[:,2].mean()),
        'cobertura80_raw':float(np.mean([r['intervalo80'] for r in rows])) if key!='base' else None,
        'curva_over_10bins':bins}


def bootstrap(rows,a,b):
    byday=defaultdict(list)
    for r in rows:
        y=np.array(r['y']);d=float(((np.array(r[a])-y)**2).sum()-((np.array(r[b])-y)**2).sum())
        byday[r['fecha']].append(d)
    days=list(byday);rng=np.random.default_rng(20261026);values=[]
    for _ in range(200):
        sample=rng.integers(0,len(days),len(days));values.append(np.mean([v for i in sample for v in byday[days[i]]]))
    return [float(x) for x in np.quantile(values,[.025,.975])]


def preparar(snapshot,code):
    if code=='wnba':return snapshot[code]
    raw=[r for r in snapshot[code] if r['tipo_partido']=='REG']
    # Validación estructural compartida, sin reclasificar el dominio original.
    # final_valido de Euroliga exige su código; el adaptador explícito sólo se
    # usa aquí para los cuatro periodos/FT/OT y deja el snapshot NBA intacto.
    rows=euro.preparar_filas([{**r,'competicion_codigo':'euroleague'} for r in raw],'2026-10-27')
    for r in rows:
        r['fecha']=r['fecha_partido'];r['y']=[r[f'{l}_q{i}'] for l in ('local','visitante') for i in range(1,5)]
    return rows


def ajustar(train,code):
    if code=='wnba':return wnba.ajustar(train,180)
    if code=='euroleague':return euro._ajustar(train)
    indices={n:i for i,n in enumerate(sorted({normalizar_nombre(r[k]) for r in train for k in ('local','visitante')}))}
    eq,rv,lc,ye,yr=[],[],[],[],[]
    for r in train:
        eq.extend([r['local'],r['visitante']]);rv.extend([r['visitante'],r['local']]);lc.extend([1,0])
        ye.extend([r['y'][:4],r['y'][4:]]);yr.extend([r['y'][4:],r['y'][:4]])
    x=construir_matriz_diseno(eq,rv,lc,indices)
    we,_=ajustar_ridge(x,np.array(ye),ALPHA_RIDGE);wr,_=ajustar_ridge(x,np.array(yr),ALPHA_RIDGE)
    return {'entidades':indices,'pesos_equipo':we.tolist(),'pesos_rival':wr.tolist(),
        'muestras_equipo':dict(Counter(normalizar_nombre(r[k]) for r in train for k in ('local','visitante'))),'alpha':ALPHA_RIDGE}


def conocido(m,r,code):
    return wnba.conocido(m,r) if code=='wnba' else euro._conocido(m,r)


def medias(m,rows,code):
    return wnba.medias(m,rows) if code=='wnba' else euro._medias(m,rows)


def evaluar(snapshot,code,out,protocolo_sha):
    rows=preparar(snapshot,code);rows=sorted([r for r in rows if r['fecha']<'2026-10-27' and r.get('fase',r.get('tipo_partido'))=='REG'],key=lambda r:(r['fecha'],r['id']))
    cut1,cut2,cut3=('2024-01-01','2024-07-15','2025-01-01') if code=='wnba' else ('2024-07-01','2025-01-01','2025-07-01')
    train=[r for r in rows if r['fecha']<cut1];disp=[r for r in rows if cut1<=r['fecha']<cut2]
    cal=[r for r in rows if cut2<=r['fecha']<cut3];test=[r for r in rows if r['fecha']>=cut3]
    m=ajustar(train,code);disp=[r for r in disp if conocido(m,r,code)]
    if len(disp)<40:raise ValueError('CAL dispersión insuficiente')
    err=np.array([r['y'] for r in disp])-medias(m,disp,code)
    cov=err.T@err/len(err);cov=.9*cov+.1*np.diag(np.diag(cov))+np.eye(8)*1e-6
    base_mu=np.array([r['y'] for r in train]).mean(axis=0)
    be=np.array([r['y'] for r in disp])-base_mu;bc=.9*(be.T@be/len(be))+.1*np.diag(np.diag(be.T@be/len(be)))+np.eye(8)*1e-6
    markets={'Q'+str(i+1):[i,i+4] for i in range(4)};markets['COMPLETO']=list(range(8))
    lines={k:[math.floor(float(base_mu[ix].sum()))+.5]+([] if code=='nba' else [round(float(base_mu[ix].sum()))]) for k,ix in markets.items()}
    candidate={'liga':code,'coeficientes':m,'covarianza':cov.tolist(),'base_media':base_mu.tolist(),'base_covarianza':bc.tolist(),
        'lineas_train':lines,'train_ids':[r['id'] for r in train],'dispersion_ids':[r['id'] for r in disp],
        'cal_ids':[r['id'] for r in cal],'test_ids':[r['id'] for r in test],'protocolo_sha256':protocolo_sha,
        'tipo':'candidato_temporal_regulacion_gaussiana_no_refit_servido','calibracion':'SIN_CALIBRAR','promovido':False}
    guardar(out/(code+'_candidato.json'),candidate)
    buckets={'CAL':defaultdict(list),'TEST':defaultdict(list)};abstenciones=[]
    with (out/(code+'_cohorte.jsonl')).open('w') as dest:
        for block,cohort in [('CAL',cal),('TEST',test)]:
            for r in cohort:
                if not conocido(m,r,code):abstenciones.append({'id':r['id'],'bloque':block,'motivo':'Equipo no soportado por TRAIN'});continue
                mu=medias(m,[r],code)[0]
                for q in range(1 if code=='nba' else 4):
                    partials=[[r['y'][i],r['y'][i+4]] for i in range(q)]
                    try:
                        cm,cc,_=condicionar(mu,cov,partials);bm,bb,_=condicionar(base_mu,bc,partials)
                    except ValueError as exc:
                        abstenciones.append({'id':r['id'],'bloque':block,'corte':q,'motivo':str(exc)});continue
                    for key,ix in markets.items():
                        if key!='COMPLETO' and int(key[1])<=q:continue
                        valor=sum(r['y'][i] for i in ix);mean=float(cm[ix].sum());var=float(cc[np.ix_(ix,ix)].sum())
                        bmean=float(bm[ix].sum());bvar=float(bb[np.ix_(ix,ix)].sum());sd=math.sqrt(var)
                        for line in lines[key]:
                            raw=wnba.probabilidades(mean,var,line);base=wnba.probabilidades(bmean,bvar,line)
                            item={'id':r['id'],'fecha':r['fecha'],'bloque':block,'liga':code,'mercado':key,'corte':q,'linea':line,
                                'entera':float(line).is_integer(),'valor':valor,'mu':mean,'base_mu':bmean,
                                'raw':list(raw.values()),'base':list(base.values()),'y':[int(valor>line),int(valor<line),int(valor==line)],
                                'intervalo80':abs(valor-mean)<=1.2815515655*sd}
                            buckets[block][f'{q}:{key}:{line}'].append(item)
                            dest.write(json.dumps(item)+'\n')
    results={}
    for key,ts in buckets['TEST'].items():
        temp,reason=calibrar(buckets['CAL'][key])
        for r in ts:r['calibrado']=temperatura(r['raw'],temp).tolist() if temp is not None else r['raw']
        ms={k:metricas(ts,k) for k in ('raw','base','calibrado')}
        ci=bootstrap(ts,'calibrado','raw') if temp is not None else None
        reasons=[]
        if temp is None:reasons.append(reason)
        if len(ts)<300:reasons.append('TEST<300')
        if len(ts)/len(test)<.9:reasons.append('Cobertura<90%')
        if ms['raw']['brier']-ms['calibrado']['brier']<.002:reasons.append('Mejora Brier<0.002')
        if ms['raw']['logloss']-ms['calibrado']['logloss']<.005:reasons.append('Mejora log loss<0.005')
        if ms['calibrado']['brier']>ms['base']['brier'] or ms['calibrado']['logloss']>ms['base']['logloss']:reasons.append('No supera referencia en ambas métricas')
        if ci is None or ci[1]>=0:reasons.append('IC95%Brier no demuestra mejora')
        reasons.append('Prospectiva independiente0/200')
        results[key]={'cal_n':len(buckets['CAL'][key]),'test_denominador':len(test),'cobertura':len(ts)/len(test),
            'temperatura':temp,'metricas':ms,'ic95_delta_brier_vs_raw':ci,'publicar':False,'bloqueos':reasons}
    result={'liga':code,'train_n':len(train),'cal_dispersion_n':len(disp),'cal_calibrador_n':len(cal),'test_n':len(test),
        'train_fin_exclusivo':cut1,'disp_fin_exclusivo':cut2,'cal_fin_exclusivo':cut3,'resultados':results,'abstenciones':abstenciones,
        'modelo_publicado':False,'prospectiva_n':0,'limite':'Candidato temporal de regulación, no calibración del artefacto activo ni del refit histórico por alcance. WNBA Gaussian no equivale a Sobol/OTv2. NBA cortes/enteras, ganador y ajustes contextuales no certificados por esta cohorte.'}
    guardar(out/(code+'_metricas.json'),result)
    return {k:v for k,v in result.items() if k not in ('resultados','abstenciones')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--protocolo',type=Path,required=True);p.add_argument('--salida',type=Path,required=True)
    a=p.parse_args();a.salida.mkdir(mode=0o700,parents=True,exist_ok=False)
    snapshot=json.loads(a.snapshot.read_text());sha=hashlib.sha256(a.protocolo.read_bytes()).hexdigest()
    guardar(a.salida/'entrada.json',{'snapshot_sha256':hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),'protocolo_sha256':sha})
    for code in ('nba','euroleague','wnba'):
        print(json.dumps(evaluar(snapshot,code,a.salida,sha)),flush=True)


if __name__=='__main__':main()
