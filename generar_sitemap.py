#!/usr/bin/env python3
"""Genera sitemap.xml y robots.txt.

El sitemap lista la portada y la ficha de cada obra. Antes listaba los PDF
directamente, y Google los indexa peor que una página HTML: de 746 fichas solo
tenía una página indexada.

    python3 generar_sitemap.py
"""
import csv
import datetime
import os
import re
import unicodedata
from xml.sax.saxutils import escape

SITIO = "https://tintaydatos.com"
SALIDA = "obras-web"
hoy = datetime.date.today().isoformat()


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "obra"


def nombre_ficha(titulo, autor, limite=45):
    """Nombre de archivo corto y legible para la ficha.

    Con entidades largas salían cosas como
    «biblioteca-digital-del-patrimonio-iberoamericano-asociacion-de-biblioteca»:
    se recorta el título por palabras completas y del autor se toma solo lo
    más distintivo, que suele ser el apellido o las primeras palabras.
    """
    t = slug(titulo)
    if len(t) > limite:
        # El número de tomo suele ir al final y es lo que distingue un volumen
        # de otro: «...de la Nueva España, tomo I» y «tomo II» quedarían con el
        # mismo nombre si se recortara sin más.
        cola = t.rsplit("-", 2)[-2:]
        sufijo = "-".join(x for x in cola
                          if x in ("i", "ii", "iii", "iv", "v", "vi", "vii",
                                   "viii", "ix", "x", "2", "3", "4")
                          or (x.isdigit() and len(x) <= 2))
        t = t[:limite].rsplit("-", 1)[0] or t[:limite]
        if sufijo and not t.endswith(sufijo):
            t = f"{t}-{sufijo}"
    # De entidades largas —«Asociación de Bibliotecas Nacionales de
    # Iberoamérica»— sobra casi todo: se quitan las palabras genéricas y se
    # conserva lo que identifica. En personas eso deja nombre y apellido.
    partes = [p for p in slug(autor).split("-") if p not in
              ("de", "la", "el", "los", "las", "y", "del", "e", "da", "dos",
               "asociacion", "ministerio", "universidad", "consejo", "nacional",
               "nacionales", "biblioteca", "bibliotecas", "instituto",
               "sociedad", "programa", "red", "agencia", "comision")]
    a = "-".join(partes[-2:]) if partes else ""
    # El nombre completo solo si el resultado sigue siendo manejable
    if len(t) + len(a) + 1 > limite + 20:
        a = partes[-1] if partes else ""
    return f"{t}-{a}".strip("-") if a else t


urls = [(SITIO + "/", "1.0")]
vistos = set()
for r in csv.DictReader(open("catalogo.csv", encoding="utf-8")):
    nombre = nombre_ficha(r["titulo"], r["autor"])
    if nombre in vistos:
        nombre = f"{nombre}-{r['id']}"
    vistos.add(nombre)
    urls.append((f"{SITIO}/{SALIDA}/{nombre}.html", "0.8"))

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for u, prio in urls:
        f.write(f"  <url>\n    <loc>{escape(u)}</loc>\n"
                f"    <lastmod>{hoy}</lastmod>\n"
                f"    <priority>{prio}</priority>\n  </url>\n")
    f.write("</urlset>\n")

with open("robots.txt", "w", encoding="utf-8") as f:
    f.write("User-agent: *\n"
            "Allow: /\n"
            "\n"
            "# Rutas que solo prueban los escáneres automáticos\n"
            "Disallow: /config/\n"
            "Disallow: /configs/\n"
            "Disallow: /development/\n"
            "\n"
            f"Sitemap: {SITIO}/sitemap.xml\n")

print(f"sitemap.xml: {len(urls)} URL ({len(urls)-1} fichas de obra)")
print(f"robots.txt escrito, apunta al sitemap")
print(f"Tamaño del sitemap: {os.path.getsize('sitemap.xml')/1024:.0f} KB")
