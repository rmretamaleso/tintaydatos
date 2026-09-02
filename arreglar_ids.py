#!/usr/bin/env python3
"""Reasigna catalogo_id a las configuraciones que comparten número.

Varias tandas asignaron ids solapados, así que obras distintas escribieron la
misma fila: los cuentos de Bobadilla acabaron figurando como argentinos. Este
script conserva el id de la obra que ya está publicada en R2 y da uno nuevo a
las demás, sin tocar el resto del catálogo.

    python3 arreglar_ids.py            # muestra qué haría
    python3 arreglar_ids.py --escribir
"""
import argparse, csv, json, pathlib, sys
from collections import defaultdict

R2 = "archivos.tintaydatos.com"
ORDEN = ["slug","titulo","autor","anio","tipo","autor_slug","piezas_fuente","orden",
         "url","catalogo","fuente","catalogo_id","catalogo_campos","nivel_parte",
         "nivel_capitulo","nivel_seccion","patron_seccion","preliminares",
         "piezas_independientes","esperados","opciones"]

ap = argparse.ArgumentParser()
ap.add_argument("--escribir", action="store_true")
a = ap.parse_args()

filas = {r["id"]: r for r in csv.DictReader(open("catalogo.csv", encoding="utf-8"))}
libre = max(int(i) for i in filas) + 1

por_id = defaultdict(list)
for p in sorted(pathlib.Path("obras").glob("*.json")):
    c = json.loads(p.read_text(encoding="utf-8"))
    if "catalogo_id" in c:
        por_id[c["catalogo_id"]].append((p, c))

cambios = []
for cid, lista in sorted(por_id.items()):
    if len(lista) < 2:
        continue
    fila = filas.get(str(cid))
    # se queda con el id la obra cuyo slug coincide con el PDF publicado
    def publicada(par):
        _, c = par
        return bool(fila) and c["slug"] in (fila.get("url", "") + fila.get("urls", ""))
    lista.sort(key=publicada, reverse=True)
    for p, c in lista[1:]:
        cambios.append((p, c, cid, libre))
        libre += 1

print(f"{len(cambios)} configuración(es) con id repetido\n")
for p, c, viejo, nuevo in cambios:
    print(f"  {p.name:<28} {c['titulo'][:32]:<34} {viejo} -> {nuevo}")
    if a.escribir:
        c["catalogo_id"] = nuevo
        c = {k: c[k] for k in ORDEN if k in c}
        p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")

if a.escribir:
    print(f"\nAhora republica esas obras para que se creen sus filas:")
    print("  python3 tinta.py " +
          " ".join(str(p) for p, _, _, _ in cambios[:6]) + " … --publicar")
else:
    print("\nCorre con --escribir para aplicarlo.")
