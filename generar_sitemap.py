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


urls = [(SITIO + "/", "1.0")]
vistos = set()
for r in csv.DictReader(open("catalogo.csv", encoding="utf-8")):
    nombre = slug(r["titulo"]) + "-" + slug(r["autor"])[:24]
    if nombre in vistos:
        nombre = f"{nombre}-{r['id']}"
    vistos.add(nombre)
    urls.append((f"{SITIO}/{SALIDA}/{nombre}", "0.8"))

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
