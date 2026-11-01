"""Respaldo/verificación/restore personal en destino nuevo, sin PostgreSQL."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from servicios import almacen_personal as store


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--respaldar',action='store_true')
    modes.add_argument('--verificar',type=Path)
    modes.add_argument('--restaurar',type=Path)
    parser.add_argument('--destino',type=Path)
    args=parser.parse_args()
    if args.respaldar:result=store.respaldar()
    elif args.verificar:
        conn=store.conectar(args.verificar)
        try:
            if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Integridad no acreditada')
            state=store.leer_conn(conn)
            result=dict(revision=state['revision'],sha256=state['sha256'],consultas=len(state['datos']['cuaderno']),favoritos=len(state['datos']['favoritos']))
        finally:conn.close()
    else:
        if not args.destino:parser.error('--restaurar exige --destino nuevo; nunca se sobrescribe el almacén vigente')
        if args.destino.resolve()==store.ruta().resolve():raise ValueError('El destino no puede ser el almacén activo')
        repo=Path(__file__).resolve().parents[1]
        if args.destino.resolve().is_relative_to(repo):raise ValueError('Los datos personales deben quedar fuera del producto')
        result=store.copiar_consistente(args.restaurar,args.destino)
    print(json.dumps(dict(ok=True,**result),ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps(dict(ok=False,tipo=type(exc).__name__,mensaje='Operación no completada. Se conserva el origen y no se sobrescribe ningún destino existente.'),ensure_ascii=False))
        raise SystemExit(1)
