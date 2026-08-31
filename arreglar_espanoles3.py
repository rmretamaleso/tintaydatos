#!/usr/bin/env python3
"""Últimos dos ajustes de la tanda española.

«La Corte de los Milagros» y «Tirano Banderas» tienen un h4 que aparece bajo
distintos niveles; se declara como sección para que no se descarte.
"""
import json, pathlib

ORDEN = ["slug","titulo","autor","anio","tipo","url","catalogo","fuente","catalogo_id",
         "catalogo_campos","nivel_parte","nivel_capitulo","nivel_seccion",
         "patron_seccion","preliminares","piezas_independientes","esperados","opciones"]

for archivo in ("vi-cortemilagros", "vi-tiranobanderas"):
    p = pathlib.Path(f"obras/{archivo}.json")
    if not p.exists():
        print(f"  (no existe {archivo})"); continue
    c = json.loads(p.read_text(encoding="utf-8"))
    c["nivel_seccion"] = ["h4", "h5"]
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  {c['titulo']:<28} nivel_seccion=['h4','h5']")
