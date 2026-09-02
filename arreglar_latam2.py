#!/usr/bin/env python3
"""Declara la estructura de las obras de la segunda tanda latinoamericana.

Dos patrones: capítulos en h3 bajo partes en h2, y texto antes del primer
capítulo. Además deja constancia en el colofón de que «Aguafuertes Cariocas»
es una recopilación póstuma.
"""
import json, pathlib

ORDEN = ["slug","titulo","autor","anio","tipo","autor_slug","piezas_fuente","orden",
         "url","catalogo","fuente","catalogo_id","catalogo_campos","nivel_parte",
         "nivel_capitulo","nivel_seccion","patron_seccion","preliminares",
         "piezas_independientes","esperados","opciones"]

PARTES = """ar-aguafuertescario ar-aguafuertesporte ar-amorbrujo ar-cienciasocultasc
ar-fabricantefantas ar-lanzallamas ar-nuevasaguafuerte ar-pruebaamor ar-saveriocruel
ar-sietelocos ar-trescientosmillo fm-cuentosfraymocho fm-memoriasvigilant
jt-viajeislamallorc rp-calvariotabor rp-cuentosgeneral rp-dosemparedadas
rp-martingaratuza rp-memoriasimpostor rp-monjacasadavirge rp-piratasgolfo
rp-vueltamuertos rd-cuentosnotas fa-historiacompania bf-cuentospoeta
lb-gotassangrecrime lb-huellasliteraria pp-hombremuertopunt""".split()

PRELIM = """ar-amorbrujo ar-cienciasocultasc ar-pruebaamor rd-asesinatopalmaso
rd-chachalaca rd-misamadrugada rd-miunicamentira rd-torooo pp-comediainmortal
pp-debora pp-hombremuertopunt lb-huellasliteraria""".split()

n = 0
for archivo in set(PARTES) | set(PRELIM):
    p = pathlib.Path(f"obras/{archivo}.json")
    if not p.exists():
        print(f"  (no existe {archivo})"); continue
    c = json.loads(p.read_text(encoding="utf-8"))
    if archivo in PARTES:
        c["nivel_parte"] = "h2"
        c["nivel_capitulo"] = "h3"
        c["nivel_seccion"] = "h4"
    if archivo in PRELIM:
        c["preliminares"] = True
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n += 1

# la agrupación de «Aguafuertes Cariocas» es póstuma y ajena: se declara
p = pathlib.Path("obras/ar-aguafuertescario.json")
if p.exists():
    c = json.loads(p.read_text(encoding="utf-8"))
    c.setdefault("fuente", {})["nota"] = (
        "Crónicas que Arlt escribió desde Brasil para el diario El Mundo en 1930 "
        "y que nunca reunió en libro. La agrupación en volumen es póstuma y ajena "
        "al autor; el texto es suyo y de dominio público.")
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  Aguafuertes Cariocas: agrupación póstuma declarada en el colofón")

print(f"{n} configuraciones corregidas")
