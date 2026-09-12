#!/usr/bin/env python3
"""Genera una página propia por obra, para que cada una sea indexable.

El sitio es un solo index.html donde el catálogo se dibuja con JavaScript, así
que Google solo puede indexar la portada: de 746 fichas tenía una sola página
indexada. Con esto cada obra tiene su URL, con su procedencia y su enlace de
descarga, y puede compartirse y encontrarse por su nombre.

    python3 generar_fichas.py             # muestra qué haría
    python3 generar_fichas.py --escribir

Las páginas se escriben en obras-web/ y el Worker las sirve tal cual, porque
publica el repositorio entero.
"""
import argparse
import csv
import html
import pathlib
import re
import unicodedata

SITIO = "https://tintaydatos.com"
R2 = "archivos.tintaydatos.com"
SALIDA = "obras-web"

PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{titulo} — {autor} | Tinta y Datos</title>
<meta name="description" content="{descripcion}"/>
<link rel="canonical" href="{url_ficha}"/>
<meta property="og:type" content="book"/>
<meta property="og:title" content="{titulo} — {autor}"/>
<meta property="og:description" content="{descripcion}"/>
<meta property="og:url" content="{url_ficha}"/>
<meta property="og:site_name" content="Tinta y Datos"/>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "{titulo}",
  "author": {{ "@type": "Person", "name": "{autor}" }},
  "inLanguage": "es",
  "datePublished": "{anio_iso}",
  "isAccessibleForFree": true,
  "url": "{url_ficha}"{bloque_descarga}
}}
</script>
<style>
  :root{{ --tinta:#1c2b4a; --tinta-clara:#4a5a7a; --malva:#6B4C8C; --verde:#a9cc6b; }}
  *{{ box-sizing:border-box; }}
  body{{
    margin:0; padding:32px 20px 64px;
    background:var(--verde); color:var(--tinta);
    font-family:Georgia,'Times New Roman',serif; line-height:1.6;
  }}
  .caja{{ max-width:720px; margin:0 auto; background:#f7f7ef;
          padding:36px 40px; border-radius:6px; }}
  .volver{{ display:inline-block; margin-bottom:24px;
            font-family:'IBM Plex Mono',monospace; font-size:12px;
            text-transform:uppercase; letter-spacing:.05em;
            color:var(--tinta); text-decoration:none; }}
  .volver:hover{{ text-decoration:underline; }}
  h1{{ font-size:30px; margin:0 0 4px; line-height:1.25; }}
  .autor{{ font-style:italic; font-size:18px; color:var(--tinta-clara);
           margin:0 0 4px; }}
  .meta{{ font-family:'IBM Plex Mono',monospace; font-size:12px;
          text-transform:uppercase; letter-spacing:.05em;
          color:var(--tinta-clara); margin:0 0 24px; }}
  .descarga{{ display:inline-block; margin:8px 0 28px; padding:11px 22px;
              background:var(--malva); color:#fff; text-decoration:none;
              border-radius:4px; font-family:'IBM Plex Mono',monospace;
              font-size:13px; }}
  .descarga:hover{{ background:#573d70; }}
  h2{{ font-size:13px; font-family:'IBM Plex Mono',monospace;
       text-transform:uppercase; letter-spacing:.06em;
       color:var(--tinta-clara); margin:26px 0 8px; font-weight:600; }}
  p{{ margin:0 0 12px; }}
  .fuente{{ font-size:14px; color:var(--tinta-clara); }}
  ol{{ margin:8px 0 0; padding-left:22px; font-size:14px;
       columns:2; column-gap:28px; }}
  li{{ margin:0 0 3px; break-inside:avoid; }}
  .pie{{ margin-top:34px; padding-top:16px;
         border-top:1px solid rgba(28,43,74,.15);
         font-size:12.5px; color:var(--tinta-clara); }}
  @media (max-width:560px){{ .caja{{ padding:26px 22px; }} ol{{ columns:1; }} }}
</style>
</head>
<body>
<div class="caja">
  <a class="volver" href="{sitio}/">← Tinta y Datos</a>
  <h1>{titulo}</h1>
  <p class="autor">{autor}{fechas}</p>
  <p class="meta">{meta}</p>
  {descarga}
  {procedencia}
  {nota_editorial}
  {piezas}
  <p class="pie">Ficha del catálogo <a href="{sitio}/">Tinta y Datos</a>,
     un índice de literatura y ciencia latinoamericana y española
     en dominio público.</p>
</div>
</body>
</html>
"""


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


def e(t):
    return html.escape(str(t or ""), quote=True)


def ficha(r, fechas_autor):
    propia = R2 in r.get("url", "") or R2 in r.get("urls", "")
    enlaces = ([p.split("::")[-1].strip() for p in r["urls"].split("|")]
               if r.get("urls", "").strip() else [r["url"]])
    nombre = nombre_ficha(r["titulo"], r["autor"])
    url_ficha = f"{SITIO}/{SALIDA}/{nombre}.html"

    partes = [x for x in (r.get("genero"), r.get("pais"), r.get("anio")) if x]
    meta = " · ".join(partes)

    desc = (f"{r['titulo']}, de {r['autor']}"
            + (f" ({r['anio']})" if r.get("anio") else "")
            + ". "
            + ("Edición propia de Tinta y Datos, tipografiada a partir de "
               "un texto verificado." if propia else
               "Ficha del catálogo con enlace a la fuente original."))

    if propia and len(enlaces) > 1:
        botones = "\n  ".join(
            f'<a class="descarga" href="{e(u)}">Descargar parte {i}</a>'
            for i, u in enumerate(enlaces, 1))
    elif propia:
        botones = f'<a class="descarga" href="{e(enlaces[0])}">Descargar el PDF</a>'
    else:
        botones = f'<a class="descarga" href="{e(enlaces[0])}">Ver en la fuente</a>'

    proc = ""
    if r.get("fuente"):
        proc = (f'<h2>Procedencia</h2><p class="fuente">Texto cotejado contra '
                f'{e(r["fuente"])}.</p>')
    if r.get("notas", "").strip():
        proc += f'<p class="fuente">{e(r["notas"])}</p>'

    nota_ed = ""
    if r.get("nota_editorial", "").strip():
        nota_ed = (f'<h2>Nota editorial</h2>'
                   f'<p class="fuente">{e(r["nota_editorial"])}</p>')

    piezas_html = ""
    trozos = [p.strip() for p in r.get("piezas", "").split(" | ") if p.strip()]
    if trozos:
        items = "".join(f"<li>{e(t)}</li>" for t in trozos)
        piezas_html = (f'<h2>{len(trozos)} textos en este volumen</h2>'
                       f'<ol>{items}</ol>')

    anio = re.match(r"\d{4}", str(r.get("anio", "")))
    bloque_descarga = ""
    if propia:
        bloque_descarga = f',\n  "encodingFormat": "application/pdf"'

    return nombre, PLANTILLA.format(
        titulo=e(r["titulo"]), autor=e(r["autor"]),
        fechas=f" ({e(fechas_autor)})" if fechas_autor else "",
        meta=e(meta), descripcion=e(desc[:300]),
        url_ficha=url_ficha, sitio=SITIO,
        anio_iso=anio.group(0) if anio else "",
        bloque_descarga=bloque_descarga,
        descarga=botones, procedencia=proc,
        nota_editorial=nota_ed, piezas=piezas_html)


def fechas_de_autores(ruta="autores.csv"):
    try:
        reg = {r["nombre"]: r for r in csv.DictReader(open(ruta, encoding="utf-8"))}
    except OSError:
        return {}
    out = {}
    for nombre, r in reg.items():
        nac, mue = r.get("nacimiento", "").strip(), r.get("muerte", "").strip()
        if mue:
            out[nombre] = f"{nac}-{mue}" if nac else f"m. {mue}"
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="catalogo.csv")
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args()

    fechas = fechas_de_autores()
    filas = list(csv.DictReader(open(a.csv, encoding="utf-8")))
    destino = pathlib.Path(SALIDA)
    if a.escribir:
        destino.mkdir(exist_ok=True)

    nombres, repetidos = set(), 0
    for r in filas:
        nombre, contenido = ficha(r, fechas.get(r["autor"], ""))
        if nombre in nombres:                 # dos obras con el mismo título
            repetidos += 1
            nombre = f"{nombre}-{r['id']}"
            nombre, contenido = nombre, contenido.replace(
                f"/{SALIDA}/{nombre}.html", f"/{SALIDA}/{nombre}-{r['id']}.html")
        nombres.add(nombre)
        if a.escribir:
            (destino / f"{nombre}.html").write_text(contenido, encoding="utf-8")

    print(f"{len(filas)} fichas | {repetidos} con nombre repetido (se les añadió el id)")
    if a.escribir:
        print(f"Escritas en {SALIDA}/")
        print("Ahora corre  python3 generar_sitemap.py  para que las liste.")
    else:
        print("Corre con --escribir para generarlas.")
