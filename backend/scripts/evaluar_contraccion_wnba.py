"""Evaluación offline explícita; nunca escribe rutas activas ni consulta red/BD."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motor.contraccion_wnba_experimental import ejecutar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--publicacion", type=Path, required=True)
    p.add_argument("--salida", type=Path, required=True)
    args = p.parse_args()
    raiz = Path(__file__).resolve().parents[2]
    destino = args.salida.resolve()
    if destino.is_relative_to(raiz) or destino == args.publicacion.resolve():
        p.error("La salida debe ser externa al repositorio y distinta del origen")
    if destino.exists():
        p.error("La salida ya existe; no se sobrescriben experimentos")
    datos = args.publicacion.read_bytes()
    politica = json.loads((raiz / "docs/reactivacion_single_user/PROTOCOLO_CONTRACCION_WNBA_2026-10-30.json").read_text(encoding="utf-8"))
    r = ejecutar(json.loads(datos.decode("utf-8")), politica)
    r["archivo_publicacion_sha256"] = hashlib.sha256(datos).hexdigest()
    if args.publicacion.read_bytes() != datos:
        raise RuntimeError("El origen cambió durante el cálculo")
    with destino.open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({"salida": str(destino), "cobertura": r["cobertura"], "activado": False}))


if __name__ == "__main__":
    main()
