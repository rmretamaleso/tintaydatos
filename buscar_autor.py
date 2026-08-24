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
import time
import unicodedata
from pathlib import Path

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


def pedir(url, intentos=3, espera=45):
    import requests
    ultimo = ""
    for n in range(intentos):
        try:
            r = requests.get(url, timeout=espera,
                             headers={"User-Agent": "TintaYDatos/1.0"})
        except requests.RequestException as e:
            ultimo = f"error de red: {type(e).__name__}"
            time.sleep(2 * (n + 1))      # el servidor a veces tarda; insistir
            continue
        if r.status_code == 404:
            return None, "404"
        if r.status_code != 200:
            ultimo = f"HTTP {r.status_code}"
            time.sleep(2 * (n + 1))
            continue
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = "utf-8"
        return r.text, None
    return None, ultimo


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


INDICE = "autores_textosinfo.tsv"


def indice(refrescar=False):
    """Nombre y slug de los 700+ autores del sitio. Se descarga una vez."""
    ruta = Path(INDICE)
    if ruta.exists() and not refrescar:
        return [tuple(l.split("\t")) for l in
                ruta.read_text(encoding="utf-8").splitlines() if "\t" in l]
    print("  descargando el índice de autores del sitio…", flush=True)
    doc, err = pedir(f"{BASE}/autores/alfabetico/pag/todas")
    if doc is None:
        print(f"  no pude descargar el índice ({err})")
        return []
    vistos, pares = set(), []
    for m in re.finditer(r'href="(?:\./|/)?([a-z0-9][a-z0-9-]*)"[^>]*>(.*?)</a>',
                         doc, re.S):
        slug, nombre = m.group(1), _limpiar_txt(m.group(2))
        if not nombre or slug in vistos or "/" in slug:
            continue
        if slug in ("autores", "libros", "textos", "buscar", "contacto"):
            continue
        vistos.add(slug)
        pares.append((nombre, slug))
    if pares:
        ruta.write_text("\n".join(f"{n}\t{s}" for n, s in pares), encoding="utf-8")
        print(f"  índice guardado en {INDICE} ({len(pares)} autores)")
    return pares


def _limpiar_txt(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", _html.unescape(s)).strip()


def buscar_en_indice(nombre):
    """Devuelve los slugs cuyo nombre contiene todas las palabras buscadas."""
    palabras = [p for p in re.split(r"\W+", _quitar_tildes(nombre)) if len(p) > 2]
    if not palabras:
        return []
    salida = []
    for n, s in indice():
        base = _quitar_tildes(n)
        if all(p in base for p in palabras):
            salida.append((n, s))
    return salida


def _quitar_tildes(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


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

        # El listado viene paginado de 24 en 24: hay que recorrerlo hasta agotarlo.
        pagina = 1
        if total > len(obras):
            print(f"  recorriendo el listado de {total} obras…", flush=True)
        while total and len(obras) < total and pagina < 80:
            pagina += 1
            time.sleep(0.4)                     # no atropellar al servidor
            mas, err = pedir(f"{BASE}/libros/autor/{slug}/pag/{pagina}")
            if mas is None:
                print(f"  AVISO: la página {pagina} no respondió ({err}); "
                      f"quedan {total - len(obras)} obras sin listar.")
                print(f"  Reintenta, o usa --filtro para acotar la búsqueda.")
                break
            nuevas = [o for o in obras_de(mas, slug) if o not in obras]
            if not nuevas:
                print(f"  AVISO: la página {pagina} no aportó obras nuevas; "
                      f"quedan {total - len(obras)} sin listar.")
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

    if not usar_slug:
        # El sitio nombra a algunos autores de forma más larga que la habitual
        # (Cervantes va bajo «miguel-de-cervantes-saavedra», Clarín bajo
        # «leopoldo-alas-clarin»). Antes de descartarlo, se consulta su índice.
        candidatos = buscar_en_indice(nombre)
        nuevos = [(n, s) for n, s in candidatos if s not in slugs]
        if len(nuevos) == 1:
            print(f"\n  el sitio lo tiene como «{nuevos[0][0]}» -> /{nuevos[0][1]}")
            return revisar(nuevos[0][1], True, filtro)
        if len(nuevos) > 1:
            print(f"\n{'='*66}\n{nombre}  ->  varias coincidencias en el índice\n{'='*66}")
            for n, s in nuevos:
                print(f"  {n[:44]:<46} --slug {s}")
            return False

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
    ap.add_argument("--refrescar-indice", action="store_true",
                    help="vuelve a descargar el índice de autores del sitio")
    ap.add_argument("--filtro", help="mostrar solo las obras cuyo título o slug "
                                     "calce con esta expresión, ej: --filtro regenta")
    a = ap.parse_args()
    try:
        import requests  # noqa: F401
    except ImportError:
        sys.exit("Falta requests:  pip install requests --break-system-packages")

    if a.refrescar_indice:
        indice(refrescar=True)
    hallados = sum(revisar(n, a.slug, a.filtro) for n in a.nombres)
    print(f"\n{hallados}/{len(a.nombres)} encontrados.")
