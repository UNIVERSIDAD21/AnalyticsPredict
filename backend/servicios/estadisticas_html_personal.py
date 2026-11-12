"""Lectura pura de capturas públicas revisadas; no descarga ni aplica datos.

Uso personal acotado con atribución a ScoreMondo. No habilita un scraper masivo
ni presume independencia de su proveedor respecto de ESPN.
"""
from datetime import datetime, timedelta
from hashlib import sha256
import html
import json
import re
from urllib.parse import urlsplit

from servicios.resolucion_multifuente_futbol import EvidenciaCampo, METODO_IDENTIDAD_ESTRICTA

METRICAS = {'Córneres':('local_corners_total','visitante_corners_total'),
            'Tiros totales':('local_disparos_total','visitante_disparos_total'),
            'Tiros a puerta':('local_disparos_arco','visitante_disparos_arco')}


def extraer_captura(raw, meta, row, vinculo):
    """Requiere vínculo revisado con IDs y nombres literales de ambos equipos."""
    if sha256(raw).hexdigest()!=meta['sha256'] or meta.get('http')!=200:
        raise ValueError('Captura sin integridad HTTP/SHA acreditada')
    if row['estado']!='FINALIZADO' or row.get('hubo_tiempo_extra'):
        raise ValueError('Sólo FT sin prórroga; no se infiere desglose de 90 minutos')
    if str(row['id'])!=vinculo['partido_id'] or str(row['competicion_id'])!=vinculo['competicion_id']:
        raise ValueError('El vínculo no identifica el partido y competición canónicos')
    text=raw.decode('utf-8')
    blocks=[json.loads(html.unescape(s)) for s in re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',text,re.S)]
    sports=[x for x in blocks if isinstance(x,dict) and x.get('@type')=='SportsEvent']
    if len(sports)!=1:
        raise ValueError('Evento estructurado ausente o ambiguo')
    sport=sports[0]
    url=sport['url'];parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.hostname!='scoremondo.com' or url!=meta['url']:
        raise ValueError('URL de captura distinta de la identidad estructurada')
    if not parsed.path.endswith('-'+vinculo['evento_web']):
        raise ValueError('ID de evento web distinto')
    if sport.get('superEvent',{}).get('name')!=vinculo['competicion_nombre']:
        raise ValueError('Competición publicada distinta de la revisada')
    # El sitio puede mantener EventScheduled en finales: exigir cierre del
    # LiveBlog del MISMO evento, no una palabra Final en otra tarjeta de la página.
    blogs=[x for x in blocks if isinstance(x,dict) and x.get('@type')=='LiveBlogPosting'
           and x.get('about',{}).get('@id')==sport.get('@id')]
    scores=(row['local_goles_total'],row['visitante_goles_total'])
    if any(type(x) is not int or x<0 for x in scores):
        raise ValueError('Marcador canónico incompleto')
    score_pattern=rf'(?<!\d){scores[0]}\s*[-–]\s*{scores[1]}(?!\d)'
    if not re.search(score_pattern,sport.get('description','')):
        raise ValueError('FT publicado contradice el canónico')
    ends=[u for b in blogs for u in b.get('liveBlogUpdate',[]) if isinstance(u,dict)
          and str(u.get('headline','')).startswith('Final del partido')
          and re.search(score_pattern,str(u.get('headline','')))]
    if len(ends)!=1:
        raise ValueError('No existe un cierre final inequívoco para este partido')
    start=datetime.fromisoformat(sport['startDate'])
    canon=row['fecha_partido']
    if isinstance(canon,str):canon=datetime.fromisoformat(canon)
    if start.tzinfo is None or canon.tzinfo is None or abs(start-canon)>timedelta(minutes=2):
        raise ValueError('Inicio con zona horaria no concilia exactamente')
    for web_side,side in [('homeTeam','local'),('awayTeam','visitante')]:
        team=sport[web_side]
        if (team['url'].rsplit('-',1)[1]!=vinculo[side+'_web_id']
                or team['name']!=vinculo[side+'_nombre_web']
                or str(row['equipo_'+side+'_id'])!=vinculo[side+'_canonico_id']):
            raise ValueError('Localía o identidad de equipo no concilia con vínculo revisado')
    pairs={};seen=set()
    for section in re.findall(r'<div class="st-v">(.*?)</div>',text,re.S):
        match=re.fullmatch(r'<b class="num">(\d+)</b><span>(.*?)</span><b class="num">(\d+)</b>',section,re.S)
        if not match:continue
        label=html.unescape(match[2])
        if label not in METRICAS:continue
        if label in seen:raise ValueError('Métrica repetida; periodo ambiguo')
        seen.add(label)
        pairs.update(zip(METRICAS[label],(int(match[1]),int(match[3]))))
    rejected={}
    if len(pairs)==6 and not any(pairs.values()) and sum(scores)>0:
        rejected={k:'Bloque de ceros sin cobertura coherente con goles' for k in pairs}
    for side in ['local','visitante']:
        sot,total=side+'_disparos_arco',side+'_disparos_total'
        for field in [sot,total]:
            if field in pairs and pairs[field]<row[side+'_goles_total']:
                rejected[field]='Inferior a goles; no se presumen autogoles que lo justifiquen'
        total_observado=pairs.get(total,row.get(total))
        if sot in pairs and total_observado is not None and pairs[sot]>total_observado:
            rejected[sot]='Tiros a puerta exceden los tiros totales observados'
    observed=datetime.fromisoformat(meta['observado_en'])
    if observed.tzinfo is None:raise ValueError('Observación sin zona horaria')
    evidence=[EvidenciaCampo(k,v,'WEB',vinculo['evento_web'],'ScoreMondo:'+k,'All',meta['sha256'],
        observed,'SCOREMONDO_PERSONAL_FT_HTML_V2') for k,v in pairs.items() if k not in rejected]
    identities={('WEB',vinculo['evento_web']):{
        'metodo':METODO_IDENTIDAD_ESTRICTA,'canonical_competition_id':str(row['competicion_id']),
        'provider_competition_id':vinculo['competicion_web_id'],
        'canonical_home_team_id':str(row['equipo_local_id']),'provider_home_team_id':vinculo['local_web_id'],
        'canonical_away_team_id':str(row['equipo_visitante_id']),'provider_away_team_id':vinculo['visitante_web_id'],
        'canonical_start_utc':canon,'provider_start_utc':start,
        'canonical_ft':list(scores),'provider_ft':list(scores)}}
    return evidence,identities,rejected,{'valores_publicados':pairs,'url':url,'inicio_utc':start.isoformat(),
        'local':sport['homeTeam'],'visitante':sport['awayTeam'],'cierre':ends[0]['headline']}
