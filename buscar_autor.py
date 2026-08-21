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


def revisar(nombre, usar_slug, filtro=None):
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
        total = int(n.group(1)) if n else 0
        obras = obras_de(doc, slug)

        # El listado viene paginado: hay que recorrerlo hasta agotarlo.
        pagina = 1
        while total and len(obras) < total and pagina < 60:
            pagina += 1
            mas, _ = pedir(f"{BASE}/libros/autor/{slug}/pagina/{pagina}")
            if mas is None:
                break
            nuevas = [o for o in obras_de(mas, slug) if o not in obras]
            if not nuevas:
                break
            obras += nuevas

        print(f"\n{'='*66}\n{nombre}  ->  /{slug}")
        print(f"{'='*66}")
        if not obras:
            print(f"  {total or '?'} obra(s) según el contador, pero no reconocí "
                  f"los enlaces. Revísala a mano:")
            print(f"  {BASE}/libros/autor/{slug}")
            return True

        mostrar = obras
        if filtro:
            rx = re.compile(filtro, re.I)
            mostrar = [o for o in obras if rx.search(o[0]) or rx.search(o[1])]
            print(f"  {len(obras)} obra(s) en total; {len(mostrar)} calzan "
                  f"con «{filtro}»:\n")
        else:
            print(f"  {len(obras)} de {total or len(obras)} obra(s):\n")
        if not mostrar:
            print("  (ninguna calza con el filtro)")
            return True
        print(f"  {'TÍTULO':<48}SLUG")
        for titulo, obra in mostrar:
            print(f"  {titulo[:47]:<48}{obra}")
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
    ap.add_argument("--filtro", help="mostrar solo las obras cuyo título o slug "
                                     "calce con esta expresión, ej: --filtro regenta")
    a = ap.parse_args()
    try:
        import requests  # noqa: F401
    except ImportError:
        sys.exit("Falta requests:  pip install requests --break-system-packages")

    hallados = sum(revisar(n, a.slug, a.filtro) for n in a.nombres)
    print(f"\n{hallados}/{len(a.nombres)} encontrados.")
