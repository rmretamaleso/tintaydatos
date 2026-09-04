#!/usr/bin/env python3
"""Añade al registro los autores que la consulta a Wikidata no resolvió.

Son de dos clases: los que devolvían varios candidatos —homónimos reales, casi
todos padre e hijo con el mismo nombre— y los que no aparecían con la grafía
que usa el catálogo. Las fechas están verificadas una por una.

    python3 completar_a_mano.py            # muestra qué haría
    python3 completar_a_mano.py --escribir
"""
import argparse
import csv
import io

# nombre tal como figura en el catálogo -> (nacimiento, muerte, nota)
FECHAS = {
    # Tenían homónimo en Wikidata: en todos el primer candidato era el correcto
    "Alberto del Solar": (1859, 1921, "militar y escritor chileno"),
    "Almafuerte": (1854, 1917, "seudónimo de Pedro Bonifacio Palacios; poeta argentino"),
    "Manuel Payno": (1810, 1894, "novelista mexicano; no confundir con su padre, "
                                 "Manuel Payno Bustamante"),
    "Miguel Cané": (1851, 1905, "escritor argentino; no confundir con su padre, "
                                "del mismo nombre"),
    "Rafael Barrett": (1876, 1910, "narrador y ensayista español radicado en Paraguay"),
    # No aparecían con la grafía del catálogo
    "Carlos Octavio Bunge": (1875, 1918, "sociólogo y escritor argentino"),
    "Eduardo Acevedo Díaz": (1851, 1921, "novelista uruguayo"),
    "Eduardo Ladislao Holmberg": (1852, 1937, "naturalista y escritor argentino"),
    "Emilio Bobadilla": (1862, 1921, "escritor cubano"),
    "Francisco Calcagno": (1827, 1903, "escritor cubano, nacido en Güines"),
    "Francisco Campos Coello": (1841, 1916, "escritor ecuatoriano"),
    "Inca Garcilaso de la Vega": (1539, 1616, "cronista peruano"),
    "José Joaquín Fernández de Lizardi": (1776, 1827, "novelista mexicano"),
    "José Seferino Álvarez «Fray Mocho»": (1858, 1903, "escritor y periodista argentino"),
    "José de la Cuadra": (1903, 1941, "narrador ecuatoriano"),
    "Juan Antonio Argerich": (1862, 1924, "médico y novelista argentino"),
    "Juan Cortada": (1805, 1868, "escritor e historiador"),
    "Manuel Díaz Rodríguez": (1871, 1927, "novelista venezolano"),
    "Manuel Eduardo de Gorostiza": (1789, 1851, "dramaturgo mexicano"),
    "Martín García Mérou": (1862, 1905, "escritor y diplomático argentino"),
    "Miguel de Cervantes Saavedra": (1547, 1616, "novelista español"),
    "Paul Groussac": (1848, 1929, "escritor franco-argentino"),
    "Roberto Payró": (1867, 1928, "escritor y periodista argentino"),
    "Vicente Riva Palacio": (1832, 1896, "novelista e historiador mexicano"),
}

ap = argparse.ArgumentParser()
ap.add_argument("--escribir", action="store_true")
a = ap.parse_args()

registro = list(csv.DictReader(open("autores.csv", encoding="utf-8")))
cols = list(registro[0].keys())
tiene = {r["nombre"] for r in registro}

nuevos = [(n, d) for n, d in FECHAS.items() if n not in tiene]
ya = [n for n in FECHAS if n in tiene]

print(f"{len(nuevos)} por añadir | {len(ya)} ya estaban en el registro\n")
for n, (nac, mue, nota) in sorted(nuevos):
    print(f"  {n:<38} {nac}-{mue}  {nota[:44]}")

if a.escribir and nuevos:
    for n, (nac, mue, nota) in nuevos:
        fila = {c: "" for c in cols}
        fila.update({"nombre": n, "nacimiento": str(nac), "muerte": str(mue),
                     "fecha_fiable": "verificada", "notas": nota})
        registro.append(fila)
    registro.sort(key=lambda x: x["nombre"])
    o = io.StringIO()
    w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
    w.writeheader(); w.writerows(registro)
    open("autores.csv", "w", encoding="utf-8").write(o.getvalue())
    print(f"\n{len(nuevos)} fichas añadidas; el registro queda con {len(registro)}")
elif not a.escribir:
    print("\nCorre con --escribir para aplicarlo.")
