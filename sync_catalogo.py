#!/usr/bin/env python3
"""
Regenera el bloque `const CATALOGO = [...]` de index.html a partir de catalogo.csv.

El CSV pasa a ser la única fuente de verdad: se edita ahí y se corre esto.
Antes había que tocar los dos archivos a mano, con el riesgo evidente.

    python3 sync_catalogo.py                 # comprueba y avisa si hay diferencias
    python3 sync_catalogo.py --escribir      # aplica los cambios a index.html
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

# Claves del objeto JS, en orden. 'tema' no se publica en el sitio.
CLAVES = ["id", "titulo", "autor", "anio", "pais", "genero", "tema", "tipo", "fuente",
          "url", "urls", "verificado", "notas", "piezas", "nota_editorial",
          "dominio", "puede_alojarse"]
OPCIONALES = {"urls", "nota_editorial", "piezas"}   # se omiten del objeto si vienen vacías
BOOLEANAS = {"verificado"}
NUMERICAS = {"id", "anio"}


def valor(clave, bruto):
    v = (bruto or "").strip()
    if clave in BOOLEANAS:
        return v.lower() in ("true", "1", "si", "sí", "yes")
    if clave in NUMERICAS and re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def objetos(ruta_csv):
    filas = list(csv.DictReader(open(ruta_csv, encoding="utf-8")))
    # Aviso de columnas del CSV que no se exportan al sitio. Sin esto, añadir
    # una columna nueva y olvidar declararla aquí hace que el sitio muestre
    # «undefined» sin que nada falle: ya pasó con piezas, nota_editorial y tema.
    if filas:
        fuera = [c for c in filas[0] if c not in CLAVES]
        if fuera:
            print(f"  aviso: columnas del CSV que no se exportan: {', '.join(fuera)}")
    if not filas:
        sys.exit(f"{ruta_csv} está vacío.")
    faltan = [c for c in CLAVES if c not in filas[0] and c not in OPCIONALES]
    if faltan:
        sys.exit(f"Al CSV le faltan columnas: {faltan}")

    out = []
    for f in filas:
        o = {}
        for c in CLAVES:
            v = valor(c, f.get(c))
            if c in OPCIONALES and not v:
                continue
            o[c] = v
        out.append(o)
    return out


def bloque_js(objs, sangria=2):
    cuerpo = ",\n".join(
        " " * sangria + json.dumps(o, ensure_ascii=False, indent=sangria)
        .replace("\n", "\n" + " " * sangria)
        for o in objs)
    return "const CATALOGO = [\n" + cuerpo + "\n];"


def comprobar_enlaces(objs):
    """Avisos útiles antes de publicar. No aborta: son avisos."""
    for o in objs:
        for u in ([p.split("::")[-1] for p in o["urls"].split("|")]
                  if o.get("urls") else [o["url"]]):
            if u and not u.startswith(("http://", "https://")):
                print(f"  AVISO id {o['id']}: enlace sospechoso «{u[:60]}»")
        if o.get("urls") and o["urls"].split("::")[-1].split("|")[0] != o["url"]:
            if o["url"] not in o["urls"]:
                print(f"  AVISO id {o['id']}: 'url' no aparece dentro de 'urls'")
        if not o.get("verificado") and "archivos.tintaydatos.com" in o.get("url", ""):
            print(f"  AVISO id {o['id']} ({o['titulo']}): alojado en R2 pero sin verificar")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="catalogo.csv")
    ap.add_argument("--html", default="index.html")
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args()

    objs = objetos(a.csv)
    nuevo = bloque_js(objs)

    html = Path(a.html).read_text(encoding="utf-8")
    m = re.search(r"const CATALOGO = \[.*?\n\];", html, re.S)
    if not m:
        sys.exit("No encontré el bloque `const CATALOGO = [...];` en " + a.html)

    print(f"{len(objs)} obras en {a.csv}")
    con_varios = [o for o in objs if o.get("urls")]
    if con_varios:
        print(f"{len(con_varios)} con varios archivos: "
              + ", ".join(f"{o['titulo']} ({o['urls'].count('|') + 1})" for o in con_varios))
    comprobar_enlaces(objs)

    if m.group(0) == nuevo:
        print("index.html ya está al día.")
    elif a.escribir:
        Path(a.html).write_text(html[:m.start()] + nuevo + html[m.end():], encoding="utf-8")
        print(f"Actualizado: {a.html}")
    else:
        print("index.html está DESACTUALIZADO. Corre con --escribir para aplicarlo.")
        sys.exit(1)
