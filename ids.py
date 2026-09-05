#!/usr/bin/env python3
"""Elige identificadores de catálogo que no choquen con los ya usados.

Los generadores de cada tanda escogían el id inicial mirando solo catalogo.csv.
Si se preparaban dos tandas antes de publicar la primera, ambas empezaban en el
mismo número y sus obras terminaban escribiendo la misma fila: dieciocho obras
quedaron invisibles hasta que se detectó.

Uso en un generador:

    from ids import siguiente_id
    cid = siguiente_id()          # primer número libre
    ...
    cid += 1

O, para reservar un bloque de una vez:

    from ids import reservar
    ids = reservar(30)            # lista de 30 números libres
"""
import csv
import glob
import json
import pathlib


def usados(catalogo="catalogo.csv", obras="obras"):
    """Todos los ids ocupados, tanto en el catálogo como en las configuraciones.

    Mirar solo el CSV no basta: una tanda ya preparada pero aún sin publicar
    tiene sus ids en los .json y en ninguna otra parte.
    """
    vistos = set()
    try:
        for r in csv.DictReader(open(catalogo, encoding="utf-8")):
            try:
                vistos.add(int(r["id"]))
            except (KeyError, ValueError):
                pass
    except OSError:
        pass
    for p in glob.glob(str(pathlib.Path(obras) / "*.json")):
        try:
            c = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
            if "catalogo_id" in c:
                vistos.add(int(c["catalogo_id"]))
        except (OSError, ValueError, KeyError):
            pass
    return vistos


def siguiente_id(catalogo="catalogo.csv", obras="obras"):
    """Primer número libre por encima de todos los usados."""
    v = usados(catalogo, obras)
    return max(v) + 1 if v else 1


def reservar(cuantos, catalogo="catalogo.csv", obras="obras"):
    """Lista de `cuantos` ids libres y consecutivos."""
    inicio = siguiente_id(catalogo, obras)
    return list(range(inicio, inicio + cuantos))


def comprobar(obras="obras"):
    """Informa de ids repetidos entre configuraciones. Devuelve cuántos hay."""
    from collections import Counter
    cuenta = Counter()
    donde = {}
    for p in sorted(glob.glob(str(pathlib.Path(obras) / "*.json"))):
        try:
            c = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        cid = c.get("catalogo_id")
        if cid is None:
            continue
        cuenta[cid] += 1
        donde.setdefault(cid, []).append(pathlib.Path(p).name)
    repetidos = {i: n for i, n in cuenta.items() if n > 1}
    if repetidos:
        print(f"{len(repetidos)} id(s) compartidos por varias configuraciones:")
        for i in sorted(repetidos):
            print(f"  id {i}: {', '.join(donde[i])}")
        print("\nCorre  python3 arreglar_ids.py --escribir  para separarlos.")
    else:
        print("Sin ids repetidos.")
    return len(repetidos)


if __name__ == "__main__":
    print(f"siguiente id libre: {siguiente_id()}")
    print()
    comprobar()
