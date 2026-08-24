#!/usr/bin/env python3
"""
Fija el bloque "esperados" de cada obra con los conteos ya verificados.

Se corre UNA vez, después de comprobar que una tanda parsea sin avisos.
A partir de ahí, cualquier cambio en la fuente hace abortar la generación
en vez de producir una edición distinta en silencio.

    python3 fijar_esperados.py            # muestra qué haría
    python3 fijar_esperados.py --escribir
"""
import argparse
import json
from pathlib import Path

# archivo: (partes, capitulos, unidades)   partes=None -> no se comprueba
CONTEOS = {
    "pardobazan-madre":      (2, 36, 1394),
    "pardobazan-pazos":      (2, 29, 1292),
    "pardobazan-quimera":    (None, 8, 2554),
    "pardobazan-tribuna":    (None, 39, 1164),
    "blasco-arroz":          (None, 12, 1466),
    "blasco-bodega":         (None, 10, 1944),
    "blasco-calafia":        (None, 10, 1271),
    "blasco-canas":          (None, 10, 1150),
    "blasco-catedral":       (None, 9, 1143),
    "blasco-horda":          (None, 12, 2006),
    "blasco-jinetes":        (3, 15, 2065),
    "blasco-maja":           (3, 16, 1610),
    "blasco-mare":           (None, 12, 3056),
    "blasco-naranjos":       (3, 16, 1448),
    "blasco-papa":           (3, 16, 1419),
    "blasco-sangre":         (None, 10, 2187),
    "unamuno-abel":          (None, 0, 1309),
    "unamuno-amorped":       (None, 19, 1439),
    "unamuno-espejo":        (None, 0, 63),
    "unamuno-niebla":        (None, 34, 2228),
    "unamuno-paz":           (None, 5, 1910),
    "unamuno-sanmanuel":     (None, 0, 232),
    "dario-azul":            (5, 39, 1193),
    "dario-cantoerrante":    (7, 48, 1608),
    "dario-cantos":          (3, 60, 1831),
    "dario-peregrinaciones": (None, 2, 545),
    "dario-prosas":          (10, 53, 2088),
    "dario-raros":           (None, 22, 1123),
    "clarin-cuentosmorales": (None, 29, 1349),
    "clarin-regenta":        (None, 31, 6001),
    "clarin-unicohijo":      (None, 16, 1162),
}

ORDEN = ["slug", "titulo", "autor", "anio", "tipo", "url", "catalogo", "fuente",
         "catalogo_id", "catalogo_campos", "volumenes", "nivel_parte",
         "nivel_capitulo", "nivel_seccion", "patron_capitulo", "patron_seccion",
         "renombrar_capitulos", "renombrar_secciones", "orden_capitulos",
         "preliminares", "esperados", "opciones"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="obras")
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args()

    cambios, ausentes = 0, []
    for archivo, (partes, caps, unidades) in sorted(CONTEOS.items()):
        p = Path(a.dir) / f"{archivo}.json"
        if not p.exists():
            ausentes.append(archivo)
            continue
        c = json.loads(p.read_text(encoding="utf-8"))
        nuevo = {}
        if partes is not None:
            nuevo["partes"] = partes
        nuevo["capitulos"] = caps
        nuevo["unidades"] = unidades

        if c.get("esperados") == nuevo:
            print(f"  =  {archivo:<24} ya está al día")
            continue
        print(f"  {'->' if a.escribir else '  '} {archivo:<24} "
              f"{c.get('esperados') or '(sin esperados)'}  =>  {nuevo}")
        cambios += 1
        if a.escribir:
            c["esperados"] = nuevo
            # las claves fuera de ORDEN se conservan al final, nunca se pierden
            resto = [k for k in c if k not in ORDEN]
            c = {**{k: c[k] for k in ORDEN if k in c}, **{k: c[k] for k in resto}}
            p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")

    if ausentes:
        print(f"\nNo encontré: {', '.join(ausentes)}")
    print(f"\n{cambios} archivo(s) por cambiar."
          + ("" if a.escribir else "  Corre con --escribir para aplicarlo."))


if __name__ == "__main__":
    main()
