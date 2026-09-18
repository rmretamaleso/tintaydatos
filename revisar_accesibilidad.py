#!/usr/bin/env python3
"""
revisar_accesibilidad.py — comprobaciones básicas de accesibilidad sobre el
HTML generado.

No sustituye a una auditoría: las herramientas automáticas detectan una parte
de los problemas y nunca prueban conformidad. Pero los fallos que busca aquí
son los que se repiten en 764 páginas generadas por plantilla, así que
corregir la plantilla los arregla todos de una vez.

Uso:
    python3 revisar_accesibilidad.py obras-web/
    python3 revisar_accesibilidad.py index.html impressum.html
"""
import glob
import os
import re
import sys
from collections import Counter
from html.parser import HTMLParser


class Auditor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = None
        self.titulo = False
        self.en_titulo = False
        self.texto_titulo = ""
        self.encabezados = []
        self.img_sin_alt = []
        self.enlaces_vagos = []
        self.en_enlace = False
        self.texto_enlace = ""
        self.idiomas_marcados = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self.en_titulo = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.encabezados.append(int(tag[1]))
        elif tag == "img":
            if "alt" not in a:
                self.img_sin_alt.append(a.get("src", "(sin src)")[:50])
        elif tag == "a":
            self.en_enlace = True
            self.texto_enlace = ""
        if a.get("lang") and tag != "html":
            self.idiomas_marcados += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.en_titulo = False
        elif tag == "a":
            t = self.texto_enlace.strip().lower()
            if t in ("aquí", "aqui", "aquí.", "más", "mas", "leer más",
                     "click aquí", "ver", "enlace", "link", "here", "más info"):
                self.enlaces_vagos.append(t)
            self.en_enlace = False

    def handle_data(self, data):
        if self.en_titulo:
            self.texto_titulo += data
        if self.en_enlace:
            self.texto_enlace += data


def revisar(ruta):
    with open(ruta, encoding="utf-8", errors="replace") as f:
        html = f.read()
    a = Auditor()
    try:
        a.feed(html)
    except Exception:
        pass

    fallos = []
    if not a.lang:
        fallos.append("falta lang en <html>: el lector de pantalla no sabe en qué idioma leer")
    if not a.texto_titulo.strip():
        fallos.append("<title> vacío o ausente")

    h = a.encabezados
    if not h:
        fallos.append("sin encabezados: la página no tiene estructura navegable")
    else:
        if h[0] != 1:
            fallos.append(f"el primer encabezado es h{h[0]}, debería ser h1")
        if h.count(1) > 1:
            fallos.append(f"{h.count(1)} elementos h1: debería haber uno solo")
        for i in range(1, len(h)):
            if h[i] - h[i - 1] > 1:
                fallos.append(f"salto de h{h[i-1]} a h{h[i]}: los niveles no deben saltarse")
                break

    if a.img_sin_alt:
        fallos.append(f"{len(a.img_sin_alt)} imagen(es) sin atributo alt")
    if a.enlaces_vagos:
        fallos.append(f"enlaces con texto poco descriptivo: {', '.join(set(a.enlaces_vagos))}")

    # Texto en otro idioma sin marcar: habitual en un sitio en español con
    # bloques en alemán, como el Impressum.
    if re.search(r"\b(der|die|das|und|nicht|Anschrift|Inhalt)\b", html) and not a.idiomas_marcados:
        fallos.append("parece haber texto en alemán sin marcar con lang")

    return fallos


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rutas = []
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            rutas += sorted(glob.glob(os.path.join(arg, "*.html")))
        else:
            rutas.append(arg)

    resumen = Counter()
    con_fallos = 0
    ejemplos = {}
    for r in rutas:
        fallos = revisar(r)
        if fallos:
            con_fallos += 1
            for f in fallos:
                clave = re.sub(r"\d+", "N", f)
                resumen[clave] += 1
                ejemplos.setdefault(clave, r)

    print(f"Revisadas {len(rutas)} páginas. Con algún fallo: {con_fallos}")
    if not resumen:
        print("Sin incidencias en las comprobaciones básicas.")
        return
    print()
    for clave, n in resumen.most_common():
        print(f"  {n:4} páginas  {clave}")
        print(f"              ej.: {ejemplos[clave]}")
    print()
    print("Como las fichas salen de una plantilla, corregir generar_fichas.py")
    print("arregla todas a la vez. Después valida a mano con WAVE o Lighthouse:")
    print("  https://wave.webaim.org/  o  DevTools > Lighthouse > Accessibility")


if __name__ == "__main__":
    main()
