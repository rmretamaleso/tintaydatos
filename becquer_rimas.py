#!/usr/bin/env python3
"""
Baja las Rimas de Bécquer desde textos.info y las deja en un .txt estructurado.

Usa la versión HTML (/ebook), NO el PDF: el PDF de la misma fuente pierde todos
los saltos de estrofa.

Uso:
  python3 becquer_rimas.py --progreso rimas_progreso_I-XIII.txt --reporte
  python3 becquer_rimas.py --html guardado.html      # si la descarga falla
"""
import argparse, html, re, sys, unicodedata

URL = "https://www.textos.info/gustavo-adolfo-becquer/rimas/ebook"
ESPERADAS = 76

# Restos de navegación del sitio, no son texto de Bécquer
ARTEFACTOS = [r"ArribaAbajo\s*", r"Arriba\s*Abajo\s*"]


def romano(n):
    s = ""
    for v, sym in [(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),
                   (9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
        while n >= v:
            s += sym; n -= v
    return s

ORDEN = [romano(i) for i in range(1, ESPERADAS + 1)]
VALIDOS = set(ORDEN)


def bajar(url):
    try:
        import requests
    except ImportError:
        sys.exit("Falta requests:  pip install requests")
    r = requests.get(url, timeout=30, headers={"User-Agent": "TintaYDatos/1.0"})
    r.raise_for_status()
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = "utf-8"
    return r.text


def _limpiar(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\u00a0", " ").replace("\u200b", "")
    for pat in ARTEFACTOS:
        s = re.sub(pat, "", s)
    return re.sub(r"[ \t]+", " ", unicodedata.normalize("NFC", s)).strip()


def parsear(doc):
    """[(romano, [[verso, ...], ...]), ...]. Tolera h2/h3, anclas y spans."""
    heads = list(re.finditer(r"<h([23])\b[^>]*>(.*?)</h\1>", doc, flags=re.S | re.I))
    rimas = []
    for i, m in enumerate(heads):
        etiqueta = _limpiar(m.group(2))
        if etiqueta not in VALIDOS:
            continue
        fin = heads[i + 1].start() if i + 1 < len(heads) else len(doc)
        bloque = re.split(r"<(?:hr|footer)\b", doc[m.end():fin])[0]

        estrofas = []
        for p in re.findall(r"<p\b[^>]*>(.*?)</p>", bloque, flags=re.S):
            voz = bool(re.search(r"<(strong|b)\b", p))
            versos = [v for v in (_limpiar(x)
                      for x in re.split(r"<br\s*/?>", p, flags=re.I)) if v]
            if not versos:
                continue
            estrofas.append([">> " + versos[0]]
                            if (voz and len(versos) == 1) else versos)
        if estrofas:
            rimas.append((etiqueta, estrofas))

    vistos = [r for r, _ in rimas]
    if vistos != ORDEN:
        faltan = [r for r in ORDEN if r not in vistos]
        sys.exit(f"Encontré {len(vistos)} rimas de {ESPERADAS}. Faltan: {faltan or '(orden alterado)'}.\n"
                 f"Aborto para no generar una edición incompleta. "
                 f"Guarda el HTML desde el navegador y reintenta con --html.")
    return rimas


def leer_progreso(ruta):
    """Lee un .txt con formato: numeral en su línea, estrofas separadas por línea vacía."""
    lineas = open(ruta, encoding="utf-8").read().split("\n")
    rimas, actual, estrofa = [], None, []
    for ln in lineas:
        s = ln.strip()
        if s in VALIDOS and not estrofa:
            if actual:
                rimas.append(actual)
            actual, estrofa = (s, []), []
            continue
        if not s:
            if actual and estrofa:
                actual[1].append(estrofa); estrofa = []
            continue
        if actual:
            estrofa.append(s)
    if actual:
        if estrofa:
            actual[1].append(estrofa)
        rimas.append(actual)
    return rimas


def escribir_txt(rimas, salida):
    with open(salida, "w", encoding="utf-8") as f:
        f.write("Rimas\nGustavo Adolfo Bécquer\n\n")
        for rom, estrofas in rimas:
            f.write(rom + "\n")
            f.write("\n\n".join("\n".join(e) for e in estrofas))
            f.write("\n\n")
    print(f"Escrito: {salida}")


def reporte(rimas):
    COLAS = ("los", "las", "el", "la", "en", "de", "un", "una", "y", "que")
    print(f"\n{'RIMA':<9}{'ESTR':>5}{'VERSOS':>8}   AVISOS")
    for rom, estrofas in rimas:
        avisos = []
        for e in estrofas:
            for v in e:
                if v.startswith(">>") or set(v) <= set(". "):
                    continue
                if v.split()[-1].strip(".,;:!?»").lower() in COLAS:
                    avisos.append(f"¿línea truncada? «{v}»")
        n = sum(len(e) for e in estrofas)
        print(f"{rom:<9}{len(estrofas):>5}{n:>8}   {'; '.join(avisos[:2])}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="HTML local en vez de descargar")
    ap.add_argument("--progreso", help="tu .txt ya verificado (I-XIII)")
    ap.add_argument("--salida", default="rimas_completo.txt")
    ap.add_argument("--reporte", action="store_true")
    a = ap.parse_args()

    rimas = parsear(open(a.html, encoding="utf-8").read() if a.html else bajar(URL))

    if a.progreso:
        mias = leer_progreso(a.progreso)
        print(f"Uso tu versión verificada para las primeras {len(mias)} rimas.")
        rimas = mias + rimas[len(mias):]

    escribir_txt(rimas, a.salida)
    if a.reporte:
        reporte(rimas)
