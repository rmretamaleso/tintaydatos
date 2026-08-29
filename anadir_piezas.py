#!/usr/bin/env python3
"""Añade la columna 'piezas' al catálogo. Se corre una sola vez.

Después, cada --publicar la mantiene al día: guarda los títulos de los cuentos
o poemas que contiene cada volumen, para que el buscador del sitio los
encuentre aunque la ficha sea del libro completo.
"""
import csv, io

filas = list(csv.DictReader(open("catalogo.csv", encoding="utf-8")))
cols = list(filas[0].keys())
if "piezas" in cols:
    raise SystemExit("La columna 'piezas' ya existe.")
cols.insert(cols.index("nota_editorial"), "piezas")
for f in filas:
    f["piezas"] = ""
o = io.StringIO()
w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
w.writeheader(); w.writerows(filas)
open("catalogo.csv", "w", encoding="utf-8").write(o.getvalue())
print("columna 'piezas' añadida; se rellena al republicar cada obra")
