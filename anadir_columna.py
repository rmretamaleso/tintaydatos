#!/usr/bin/env python3
"""Añade la columna nota_editorial al catálogo y la rellena desde los .json.

Se corre una sola vez. Después, cada --publicar la mantiene al día.
"""
import csv, glob, io, json, os

filas = list(csv.DictReader(open("catalogo.csv", encoding="utf-8")))
cols = list(filas[0].keys())
if "nota_editorial" not in cols:
    cols.insert(cols.index("notas"), "nota_editorial")
    for f in filas:
        f["nota_editorial"] = ""

# la nota del colofón de cada obra, por catalogo_id
notas = {}
for p in glob.glob("obras/*.json"):
    c = json.load(open(p, encoding="utf-8"))
    cid = c.get("catalogo_id")
    nota = (c.get("fuente") or {}).get("nota", "").strip()
    if cid is not None and nota:
        notas[str(cid)] = nota

n = 0
for f in filas:
    if not f["nota_editorial"].strip() and f["id"] in notas:
        f["nota_editorial"] = notas[f["id"]]
        n += 1

o = io.StringIO()
w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
w.writeheader(); w.writerows(filas)
open("catalogo.csv", "w", encoding="utf-8").write(o.getvalue())
print(f"columna nota_editorial añadida; {n} fichas con nota editorial")

# Avisar de las que quedaron diciendo lo mismo dos veces
import re
def clave(t): return set(re.findall(r"[a-záéíóúñ]{5,}", t.lower()))
repes = [f for f in filas if f["nota_editorial"].strip() and f["notas"].strip()
         and len(clave(f["notas"]) & clave(f["nota_editorial"])) >= 4]
if repes:
    print(f"\n{len(repes)} ficha(s) donde 'notas' repite lo editorial; conviene acortarlas:")
    for f in repes:
        print(f"  [{f['id']:>4}] {f['titulo'][:40]}")

# Nota: donde la nota descriptiva ya contaba el trabajo editorial, queda
# repetida. Conviene revisar esas fichas y dejar la parte editorial solo en
# nota_editorial, para que 'notas' describa la obra y no el proceso.
