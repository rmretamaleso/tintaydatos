#!/usr/bin/env python3
"""Genera sitemap.xml y robots.txt para que los buscadores indexen bien.

El sitemap lista el sitio y cada PDF publicado: sin esto Google solo conoce la
portada, y las ediciones —que son lo que la gente busca— quedan invisibles.

    python3 generar_sitemap.py
"""
import csv
import datetime
import os
from xml.sax.saxutils import escape

SITIO = "https://tintaydatos.com"
R2 = "archivos.tintaydatos.com"
hoy = datetime.date.today().isoformat()

urls = [(SITIO + "/", "1.0")]
vistos = set()
for r in csv.DictReader(open("catalogo.csv", encoding="utf-8")):
    enlaces = ([p.split("::")[-1] for p in r["urls"].split("|")]
               if r.get("urls", "").strip() else [r["url"]])
    for u in enlaces:
        u = u.strip()
        if R2 in u and u not in vistos:
            vistos.add(u)
            urls.append((u, "0.8"))

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

print(f"sitemap.xml: {len(urls)} URL ({len(urls)-1} ediciones)")
print(f"robots.txt escrito, apunta al sitemap")
print(f"\nTamaño del sitemap: {os.path.getsize('sitemap.xml')/1024:.0f} KB")
