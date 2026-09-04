#!/usr/bin/env python3
"""Completa las fechas de nacimiento y muerte de los autores del catálogo.

Consulta Wikidata y guarda el resultado en autores.csv, que ya es el registro
donde viven los plazos y las notas de cada autor.

    python3 completar_autores.py            # muestra qué encontraría
    python3 completar_autores.py --escribir

Sobre los homónimos: se consideran solo los candidatos que son personas con
fecha de muerte. Una «Biblioteca Roberto Arlt» comparte el nombre pero no es
una persona, así que no crea ambigüedad. Cuando de verdad hay dos personas
distintas con el mismo nombre, el autor se deja sin completar y se lista al
final: es preferible una ficha vacía a la fecha de otra persona.
"""
import argparse
import csv
import io
import json
import time
import urllib.parse

WD = "https://www.wikidata.org/w/api.php"
AGENTE = {"User-Agent": "TintaYDatos/1.0 (catalogo de dominio publico)"}
R2 = "archivos.tintaydatos.com"


def _get(url):
    import requests
    for n in range(3):
        try:
            r = requests.get(url, timeout=60, headers=AGENTE)
            if r.status_code == 200:
                return json.loads(r.text)
        except Exception:
            pass
        time.sleep(2 * (n + 1))
    return None


def _candidatos(nombre, idioma):
    q = urllib.parse.urlencode({"action": "wbsearchentities", "search": nombre,
                                "language": idioma, "uselang": idioma,
                                "format": "json", "limit": 8, "type": "item"})
    d = _get(f"{WD}?{q}")
    return d.get("search", []) if d else []


def _fechas(qid):
    """(nacimiento, muerte) de una entidad, o (None, None) si no es persona."""
    q = urllib.parse.urlencode({"action": "wbgetentities", "ids": qid,
                                "props": "claims", "format": "json"})
    e = _get(f"{WD}?{q}")
    if not e:
        return None, None
    claims = e.get("entities", {}).get(qid, {}).get("claims", {})

    def anio(prop):
        try:
            t = claims[prop][0]["mainsnak"]["datavalue"]["value"]["time"]
            return abs(int(t[1:5])) * (-1 if t[0] == "-" else 1)
        except (KeyError, IndexError, ValueError, TypeError):
            return None

    return anio("P569"), anio("P570")


def buscar(nombre):
    """Datos del autor, o None si no se halló ninguna persona fallecida.

    Busca primero en español y, si no da resultado, en inglés: varias fichas de
    autores hispanoamericanos solo tienen etiqueta en inglés.
    """
    encontrados = {}
    for idioma in ("es", "en"):
        for c in _candidatos(nombre, idioma):
            if c["id"] in encontrados:
                continue
            nac, mue = _fechas(c["id"])
            time.sleep(0.2)
            if mue:                       # solo personas con fecha de muerte
                encontrados[c["id"]] = {
                    "nacimiento": nac, "muerte": mue,
                    "descripcion": c.get("description", ""),
                    "etiqueta": c.get("label", "")}
        if encontrados:
            break

    if not encontrados:
        return None
    personas = list(encontrados.values())
    elegido = dict(personas[0])
    # Ambigüedad real solo si otra persona comparte el nombre y murió en un año
    # distinto: dos fichas de la misma persona no cuentan.
    otros = [p for p in personas[1:] if p["muerte"] != elegido["muerte"]]
    elegido["ambiguo"] = bool(otros)
    elegido["otros"] = [f"{p['etiqueta']} ({p['nacimiento']}–{p['muerte']}, "
                        f"{p['descripcion'][:30]})" for p in otros]
    return elegido


ap = argparse.ArgumentParser()
ap.add_argument("--escribir", action="store_true")
ap.add_argument("--solo", help="completa un autor concreto")
a = ap.parse_args()

registro = list(csv.DictReader(open("autores.csv", encoding="utf-8")))
cols = list(registro[0].keys())
tiene = {r["nombre"] for r in registro}

publicados = {r["autor"] for r in csv.DictReader(open("catalogo.csv", encoding="utf-8"))
              if R2 in r["url"] or R2 in r.get("urls", "")}
faltan = sorted(publicados - tiene)
if a.solo:
    faltan = [n for n in faltan if a.solo.lower() in n.lower()]

print(f"{len(faltan)} autor(es) sin ficha\n")
nuevos, dudosos, sin_datos = [], [], []
for i, nombre in enumerate(faltan, 1):
    r = buscar(nombre)
    if not r:
        sin_datos.append(nombre)
        print(f"  {i:>3}/{len(faltan)}  {nombre:<36} sin fechas en Wikidata")
        continue
    marca = "  <- dos personas con ese nombre" if r["ambiguo"] else ""
    print(f"  {i:>3}/{len(faltan)}  {nombre:<36} {r['nacimiento']}-{r['muerte']}"
          f"  ({r['descripcion'][:30]}){marca}")
    (dudosos if r["ambiguo"] else nuevos).append((nombre, r))

if a.escribir and nuevos:
    for nombre, r in nuevos:
        fila = {c: "" for c in cols}
        fila.update({"nombre": nombre,
                     "nacimiento": str(r["nacimiento"] or ""),
                     "muerte": str(r["muerte"]),
                     "fecha_fiable": "wikidata",
                     "notas": r["descripcion"]})
        registro.append(fila)
    registro.sort(key=lambda x: x["nombre"])
    o = io.StringIO()
    w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
    w.writeheader(); w.writerows(registro)
    open("autores.csv", "w", encoding="utf-8").write(o.getvalue())
    print(f"\n{len(nuevos)} fichas anadidas a autores.csv")

print(f"\n{len(nuevos)} con fecha clara | {len(dudosos)} ambiguos | "
      f"{len(sin_datos)} sin datos")
if dudosos:
    print("\nDos personas con el mismo nombre (revisalos a mano):")
    for n, r in dudosos:
        print(f"  {n:<34} {r['nacimiento']}-{r['muerte']}  {r['descripcion'][:34]}")
        for otro in r["otros"][:2]:
            print(f"       frente a: {otro}")
if sin_datos:
    print("\nSin fechas en Wikidata:")
    for n in sin_datos:
        print(f"  {n}")
if not a.escribir:
    print("\nCorre con --escribir para guardar las fichas claras.")
