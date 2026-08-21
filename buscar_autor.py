#!/usr/bin/env python3
"""
Comprueba si un autor está en textos.info y lista sus obras disponibles.

Evita la búsqueda manual, que es el cuello de botella real del catálogo:
generar un PDF toma minutos, averiguar si una obra existe y es publicable
toma bastante más.

    python3 buscar_autor.py "Augusto d'Halmar" "Pedro Prado" "Luis Orrego Luco"
    python3 buscar_autor.py baldomero-lillo --slug

Con --slug los argumentos se toman como slugs literales, sin probar variantes.
"""
import argparse
import html as _html
import re
import sys
import unicodedata

BASE = "https://www.textos.info"


def variantes(nombre):
    """De 'Augusto d'Halmar' saca los slugs plausibles que usa el sitio."""
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    s = s.lower().strip()
    sin_apostrofo = s.replace("'", "").replace("’", "")
    con_guion = s.replace("'", "-").replace("’", "-")
    out = []
    for v in (sin_apostrofo, con_guion):
        v = re.sub(r"[^a-z0-9]+", "-", v).strip("-")
        v = re.sub(r"-{2,}", "-", v)
        if v and v not in out:
            out.append(v)
    return out


def pedir(url):
    import requests
    try:
        r = requests.get(url, timeout=30,
                         headers={"User-Agent": "TintaYDatos/1.0"})
    except requests.RequestException as e:
        return None, f"error de red: {e}"
    if r.status_code == 404:
        return None, "404"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    if not r.encoding or r.encoding.lower() == "iso-8859-1":
        r.encoding = "utf-8"
    return r.text, None


def obras_de(doc, slug):
    """Extrae (titulo, slug_obra) de la página de listado del autor."""
    vistas, out = set(), []
    # Los enlaces del sitio son relativos: href="./autor-slug/obra-slug".
    # El prefijo obligatorio evita capturar la navegación, que va bajo
    # "./libros/autor/autor-slug/...".
    patron = re.compile(
        rf'href="(?:\./|/|https?://www\.textos\.info/)?{re.escape(slug)}/'
        rf'([a-z0-9][a-z0-9-]*)"[^>]*>(.*?)</a>', re.S | re.I)
    for m in patron.finditer(doc):
        obra, titulo = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        titulo = _html.unescape(titulo).strip()
        if obra in ("ebook", "descargar-pdf", "descargar-epub") or not titulo:
            continue
        if obra in vistas:
            continue
        vistas.add(obra)
        out.append((titulo, obra))
    return out


def paginas_y_licencia(doc, obra):
    """Busca '123 págs.' y la marca de dominio público cerca del enlace."""
    i = doc.find(f"/{obra}")
    if i < 0:
        return None, None
    trozo = doc[i:i + 4000]
    pags = re.search(r"([\d.]+)\s*págs", trozo)
    dp = "Dominio público" if re.search(r"Dominio p[úu]blico", trozo) else None
    return (pags.group(1) if pags else None), dp


def revisar(nombre, usar_slug):
    slugs = [nombre] if usar_slug else variantes(nombre)
    for slug in slugs:
        doc, err = pedir(f"{BASE}/libros/autor/{slug}")
        if doc is None:
            continue
        n = re.search(r"(\d+)\s+libros? encontrados", doc)
        # El sitio devuelve 200 aunque el autor no exista; lo que lo delata
        # es el contador en cero.
        if n and n.group(1) == "0":
            continue
        obras = obras_de(doc, slug)
        print(f"\n{'='*66}\n{nombre}  ->  /{slug}")
        print(f"{'='*66}")
        if not obras:
            print(f"  {n.group(1) if n else '?'} obra(s) según el contador, pero no "
                  f"reconocí los enlaces. Revísala a mano:")
            print(f"  {BASE}/libros/autor/{slug}")
            return True
        print(f"  {n.group(1) if n else len(obras)} obra(s):\n")
        print(f"  {'TÍTULO':<44}{'PÁGS':>7}   LICENCIA")
        for titulo, obra in obras:
            pags, dp = paginas_y_licencia(doc, obra)
            print(f"  {titulo[:43]:<44}{pags or '?':>7}   {dp or '¿?'}")
        print(f"\n  Slugs: {', '.join(o for _, o in obras)}")
        return True

    print(f"\n{'='*66}\n{nombre}  ->  NO ESTÁ en textos.info")
    print(f"{'='*66}")
    print(f"  Probé: {', '.join('/' + s for s in slugs)}")
    print("  Si crees que sí está, busca el slug real en "
          f"{BASE}/autores/alfabetico y reintenta con --slug.")
    return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("nombres", nargs="+")
    ap.add_argument("--slug", action="store_true",
                    help="tratar los argumentos como slugs literales")
    a = ap.parse_args()
    try:
        import requests  # noqa: F401
    except ImportError:
        sys.exit("Falta requests:  pip install requests --break-system-packages")

    hallados = sum(revisar(n, a.slug) for n in a.nombres)
    print(f"\n{hallados}/{len(a.nombres)} encontrados.")
