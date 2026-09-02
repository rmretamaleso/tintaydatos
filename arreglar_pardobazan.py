#!/usr/bin/env python3
"""Declara la estructura de las obras de Pardo Bazán que avisaban."""
import json, pathlib

ORDEN = ["slug","titulo","autor","anio","tipo","url","catalogo","fuente","catalogo_id",
         "catalogo_campos","nivel_parte","nivel_capitulo","nivel_seccion",
         "patron_seccion","preliminares","piezas_independientes","esperados","opciones"]

# capítulos en h3 bajo partes en h2
PARTES = ["pb-cuentosnavidadanon","pb-cuentossacroprofan","pb-damajoven",
          "pb-dulcesueno","pb-insolacionmorrina","pb-misterio","pb-prueba",
          "pb-saludobrujas"]
# más un cuarto nivel
CUARTO = {"pb-misterio", "pb-saludobrujas"}
# texto antes del primer capítulo
PRELIM = {"pb-bucolica": True, "pb-saludobrujas": "Al que leyere"}

n = 0
for archivo in set(PARTES) | set(PRELIM):
    p = pathlib.Path(f"obras/{archivo}.json")
    if not p.exists():
        print(f"  (no existe {archivo})"); continue
    c = json.loads(p.read_text(encoding="utf-8"))
    if archivo in PARTES:
        c["nivel_parte"] = "h2"
        c["nivel_capitulo"] = "h3"
        if archivo in CUARTO:
            c["nivel_seccion"] = "h4"
            c["patron_seccion"] = "^(.+)$"
    if archivo in PRELIM:
        c["preliminares"] = PRELIM[archivo]
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n += 1
print(f"{n} configuraciones corregidas")
