#!/usr/bin/env python3
"""Fija el año de edición en las obras que ya estaban publicadas.

Todo lo publicado hasta ahora se compuso en 2026. De aquí en adelante tinta.py
lo escribe solo la primera vez que genera cada obra, así que este script se
corre una única vez.

    python3 fijar_anio_edicion.py            # muestra qué haría
    python3 fijar_anio_edicion.py --escribir
"""
import argparse
import json
import pathlib

ANIO = 2026
ORDEN = ["slug", "titulo", "autor", "anio", "anio_edicion", "tipo", "autor_slug",
         "piezas_fuente", "orden", "gutenberg", "wikisource", "url", "catalogo",
         "fuente", "catalogo_id", "catalogo_campos", "nivel_parte",
         "nivel_capitulo", "nivel_seccion", "patron_seccion", "preliminares",
         "piezas_independientes", "esperados", "volumenes", "catalogo_notas",
         "opciones"]

ap = argparse.ArgumentParser()
ap.add_argument("--escribir", action="store_true")
ap.add_argument("--anio", type=int, default=ANIO)
a = ap.parse_args()

sin, ya = [], 0
for p in sorted(pathlib.Path("obras").glob("*.json")):
    c = json.loads(p.read_text(encoding="utf-8"))
    if c.get("anio_edicion"):
        ya += 1
        continue
    sin.append((p, c))

print(f"{len(sin)} configuración(es) sin año de edición | {ya} ya lo tienen")
if a.escribir:
    for p, c in sin:
        c["anio_edicion"] = a.anio
        # cualquier clave que no esté en ORDEN se conserva al final
        ordenado = {k: c[k] for k in ORDEN if k in c}
        ordenado.update({k: v for k, v in c.items() if k not in ordenado})
        p.write_text(json.dumps(ordenado, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    print(f"Marcadas con anio_edicion = {a.anio}")
    print("\nPara que aparezca en los PDF hay que republicar:")
    print("  python3 tinta.py obras/*.json --publicar")
else:
    for p, _ in sin[:8]:
        print(f"  {p.name}")
    if len(sin) > 8:
        print(f"  … y {len(sin) - 8} más")
    print("\nCorre con --escribir para aplicarlo.")
