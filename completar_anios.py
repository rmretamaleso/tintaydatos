#!/usr/bin/env python3
"""Completa el año de publicación de las obras que no lo tienen.

Consulta Wikidata y acepta un resultado solo cuando la ficha menciona al autor
que figura en el catálogo. Sin esa comprobación, «Brenda» devuelve un nombre de
pila y «Nativa» una película de 1939: los títulos de una palabra tienen muchos
homónimos y el año equivocado sería peor que ninguno.

    python3 completar_anios.py            # muestra qué encontraría
    python3 completar_anios.py --escribir

Lo que no se resuelve queda sin año; fijar_anios.py lo marcará «s. f.», que es
la convención bibliográfica para una fecha que no consta.
"""
import argparse
import json
import pathlib
import re
import time
import unicodedata
import urllib.parse

WD = "https://www.wikidata.org/w/api.php"
AGENTE = {"User-Agent": "TintaYDatos/1.0 (catalogo de dominio publico)"}
ORDEN = ["slug", "titulo", "autor", "anio", "anio_edicion", "tipo", "autor_slug",
         "piezas_fuente", "orden", "gutenberg", "wikisource", "url", "catalogo",
         "fuente", "catalogo_id", "catalogo_campos", "nivel_parte",
         "nivel_capitulo", "nivel_seccion", "patron_seccion", "preliminares",
         "piezas_independientes", "esperados", "volumenes", "catalogo_notas",
         "opciones"]


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", "", s)


def _get(url):
    import requests
    for n in range(3):
        try:
            r = requests.get(url, timeout=45, headers=AGENTE)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(2 * (n + 1))
    return None


def _anio_de_entidad(qid):
    """Año de publicación declarado como propiedad (P577)."""
    q = urllib.parse.urlencode({"action": "wbgetentities", "ids": qid,
                                "props": "claims", "format": "json"})
    d = _get(f"{WD}?{q}")
    if not d:
        return None
    claims = d.get("entities", {}).get(qid, {}).get("claims", {})
    for prop in ("P577", "P571"):          # publicación, o creación
        try:
            t = claims[prop][0]["mainsnak"]["datavalue"]["value"]["time"]
            return int(t[1:5])
        except (KeyError, IndexError, ValueError, TypeError):
            continue
    return None


def buscar(titulo, autor):
    """(año, descripción) si la ficha corresponde a esta obra, o None.

    Se exige que la descripción nombre al autor: es lo que distingue «El
    combate de la tapera, 1892 short story by Eduardo Acevedo Díaz» de
    «Brenda, female given name».
    """
    apellidos = [p for p in norm(autor).split() if len(p) > 3]
    for idioma in ("es", "en"):
        q = urllib.parse.urlencode({"action": "wbsearchentities", "search": titulo,
                                    "language": idioma, "uselang": idioma,
                                    "format": "json", "limit": 6, "type": "item"})
        d = _get(f"{WD}?{q}")
        for c in (d or {}).get("search", []):
            desc = norm(c.get("description", ""))
            if not any(a in desc for a in apellidos):
                continue
            # el año suele venir en la descripción («1892 short story by…»)
            m = re.match(r"^(1[4-9]\d\d|20[0-2]\d)\b", c.get("description", ""))
            anio = int(m.group(1)) if m else _anio_de_entidad(c["id"])
            time.sleep(0.2)
            if anio:
                return anio, c.get("description", "")
    return None


ap = argparse.ArgumentParser()
ap.add_argument("--escribir", action="store_true")
ap.add_argument("--limite", type=int, help="procesa solo las primeras N")
a = ap.parse_args()

sin = []
for p in sorted(pathlib.Path("obras").glob("*.json")):
    c = json.loads(p.read_text(encoding="utf-8"))
    if not c.get("anio"):
        sin.append((p, c))
if a.limite:
    sin = sin[:a.limite]

print(f"{len(sin)} obra(s) sin año\n")
hallados, sin_suerte = [], []
for i, (p, c) in enumerate(sin, 1):
    r = buscar(c["titulo"], c.get("autor", ""))
    if r:
        anio, desc = r
        hallados.append((p, c, anio))
        print(f"  {i:>3}/{len(sin)}  {c['titulo'][:38]:<40} {anio}  ({desc[:40]})")
    else:
        sin_suerte.append(c["titulo"])
        print(f"  {i:>3}/{len(sin)}  {c['titulo'][:38]:<40} —")
    time.sleep(0.3)

if a.escribir and hallados:
    for p, c, anio in hallados:
        c["anio"] = anio
        c.setdefault("catalogo_campos", {})["anio"] = str(anio)
        ordenado = {k: c[k] for k in ORDEN if k in c}
        ordenado.update({k: v for k, v in c.items() if k not in ordenado})
        p.write_text(json.dumps(ordenado, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    print(f"\n{len(hallados)} configuraciones actualizadas")
    print("Republica esas obras para que el año llegue al catálogo y a la portada.")

print(f"\n{len(hallados)} con año | {len(sin_suerte)} sin resolver")
if not a.escribir:
    print("\nCorre con --escribir para aplicarlo.")
