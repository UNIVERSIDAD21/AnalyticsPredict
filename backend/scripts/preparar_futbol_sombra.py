"""Prepara una cohorte futura aislada; no activa ML, calibra ni escribe en BD.

La política debe declararse antes de preparar. Cada salida se crea una sola vez;
conserva coeficientes, datos, fixtures y hashes. No es un almacén inmutable de BD.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor_futbol.evaluacion.estacional import PoliticaEstacional, exigir_utc, preparar_candidato, pronosticar_sombra
from motor_futbol.modelos.artefacto import sha256


def escribir_nuevo(path, datos):
    contenido = json.dumps(datos, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    with path.open('x', encoding='utf-8') as f:
        f.write(contenido)


def cargar_partidos(path):
    datos = json.loads(path.read_text())
    partidos = datos['partidos']
    # Verificar antes de convertir fechas; un JSON alterado no conserva la huella.
    if datos.get('sha256_datos') != sha256(partidos):
        raise ValueError('El snapshot no conserva su hash de datos')
    for p in partidos:
        p['fecha_partido'] = exigir_utc(datetime.fromisoformat(p['fecha_partido']))
    return datos, partidos


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--politica', type=Path, required=True)
    parser.add_argument('--inicio', type=datetime.fromisoformat)
    parser.add_argument('--fin', type=datetime.fromisoformat)
    parser.add_argument('--declarar', action='store_true')
    parser.add_argument('--objetivo-cal', type=int, choices=[100, 200], default=200,
                        help='Reserva predeclarada; CAL mínimo100 no cambia. Cada reserva requiere nueva declaración/cohorte.')
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--fixtures', type=Path)
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args(argv)
    ahora = datetime.now(timezone.utc)
    politica = PoliticaEstacional(objetivo_cal=args.objetivo_cal,
        version='estacional_sombra_v3_cal100' if args.objetivo_cal == 100 else 'estacional_sombra_v2')
    politica.validar()
    if args.declarar:
        if not args.inicio or not args.fin or not ahora < exigir_utc(args.inicio) < exigir_utc(args.fin):
            parser.error('Declarar un periodo futuro con zona horaria')
        escribir_nuevo(args.politica, {'politica': politica.to_dict(), 'declarado_en': ahora.isoformat(),
            'inicio_eval': exigir_utc(args.inicio).isoformat(), 'fin_eval': exigir_utc(args.fin).isoformat(),
            'criterio': 'Evaluar todas las predicciones/abstenciones de la cohorte, sin seleccionar por resultado',
            'certificacion': 'NO_CERTIFICADO'})
        print('Política futura declarada; no se ajustó modelo ni se consultó BD.')
        return 0
    if not all((args.snapshot, args.fixtures, args.salida)):
        parser.error('Preparar requiere --snapshot, --fixtures y --salida')
    declaracion = json.loads(args.politica.read_text())
    declarado, inicio, fin = [exigir_utc(datetime.fromisoformat(declaracion[k]))
                             for k in ('declarado_en', 'inicio_eval', 'fin_eval')]
    if declaracion['politica'] != politica.to_dict() or not declarado < ahora < inicio < fin:
        raise ValueError('Política alterada, futura o periodo ya iniciado')
    snapshot, partidos = cargar_partidos(args.snapshot)
    fixtures, futuros = cargar_partidos(args.fixtures)
    corte = exigir_utc(datetime.fromisoformat(snapshot['observado_en']))
    observado_fixtures = exigir_utc(datetime.fromisoformat(fixtures['observado_en']))
    if not declarado <= corte < ahora or not declarado <= observado_fixtures < ahora:
        raise ValueError('La observación debe ser posterior a la declaración y anterior al congelamiento')
    if any(p['fecha_partido'] >= corte for p in partidos):
        raise ValueError('El snapshot incluye outcomes posteriores al corte')
    familias = {}
    for tipo in ('goles', 'disparos', 'corners'):
        candidato = preparar_candidato(partidos, tipo, corte, politica)
        candidato['fit_completed_at'] = datetime.now(timezone.utc).isoformat()
        familias[tipo] = {'candidato': candidato}
    congelado = datetime.now(timezone.utc)
    for familia in familias.values():
        familia['cohorte'] = pronosticar_sombra(familia['candidato'], futuros, congelado, inicio, fin)
    salida = {'declaracion': declaracion, 'declaracion_sha256': sha256(declaracion),
        'congelado_en': congelado.isoformat(), 'snapshot_sha256': snapshot['sha256_datos'],
        'fixtures_sha256': fixtures['sha256_datos'], 'familias': familias,
        'certificacion': 'NO_CERTIFICADO', 'modelo_activo': False,
        'policy': {'no_picks': True, 'no_stake': True, 'no_betting_recommendations': True}}
    salida['sha256'] = sha256(salida)
    if datetime.now(timezone.utc) >= inicio:
        raise ValueError('El periodo empezó mientras se preparaba la cohorte; no publicar tarde')
    escribir_nuevo(args.salida, salida)
    print(json.dumps({k: {'estado': v['candidato']['estado'],
        'predicciones': len(v['cohorte']['predicciones']), 'abstenciones': len(v['cohorte']['abstenciones'])}
        for k, v in familias.items()}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
