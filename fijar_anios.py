#!/usr/bin/env python3
"""Completa los años que se pudieron documentar y marca el resto como «s. f.».

Las fechas provienen de la Biblioteca Nacional de España, Cervantes Virtual y
bibliografías de referencia. Las que no constan quedan como «s. f.» —sin
fecha—, que es la convención bibliográfica: muchas de estas obras son novelas
cortas aparecidas en colecciones semanales, o recopilaciones póstumas de
material periodístico, y su año exacto no está establecido.
"""
import csv, io, json, pathlib

ANIOS = {
    # Carmen de Burgos — BNE y bibliografías de referencia
    "397": 1905,   # Alucinación
    "389": 1916,   # Confidencias
    "395": 1923,   # Los espirituados
    "393": 1924,   # La mujer fantástica
    "390": 1931,   # Quiero vivir mi vida
    "403": 1931,   # Puñal de claveles
}

filas = list(csv.DictReader(open("catalogo.csv", encoding="utf-8")))
R2 = "archivos.tintaydatos.com"
puestos = marcados = 0
for r in filas:
    if r["id"] in ANIOS:
        r["anio"] = str(ANIOS[r["id"]]); puestos += 1
    elif not r["anio"].strip() and R2 in r["url"]:
        r["anio"] = "s. f."; marcados += 1

o = io.StringIO()
w = csv.DictWriter(o, fieldnames=filas[0].keys(), lineterminator="\n")
w.writeheader(); w.writerows(filas)
open("catalogo.csv", "w", encoding="utf-8").write(o.getvalue())
print(f"{puestos} años documentados | {marcados} marcados «s. f.»")

# reflejarlo en los .json para que no se pierdan al republicar
for p in pathlib.Path("obras").glob("*.json"):
    c = json.loads(p.read_text(encoding="utf-8"))
    cid = str(c.get("catalogo_id", ""))
    if cid in ANIOS:
        c["anio"] = ANIOS[cid]
        c.setdefault("catalogo_campos", {})["anio"] = str(ANIOS[cid])
        p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("configuraciones actualizadas")
