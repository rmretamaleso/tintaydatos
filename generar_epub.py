#!/usr/bin/env python3
"""
generar_epub.py — produce un EPUB 3 accesible con la misma estructura de obra
que consume edicion.py.

Por qué EPUB además del PDF: un PDF maquetado para A5 no se adapta a una
pantalla pequeña ni a un tamaño de letra grande, y ReportLab no puede generar
PDF etiquetados, así que un lector de pantalla recorre el texto sin saber qué
es un capítulo. El EPUB resuelve las dos cosas de raíz: el texto fluye, la
estructura es semántica y la navegación por capítulos es nativa.

Se usa igual que edicion.generar:

    import generar_epub
    generar_epub.generar(obra, "epub/mi-obra-tinta-y-datos.epub")

donde `obra` es el mismo diccionario que recibe edicion.generar:
    {titulo, autor, partes: [{nombre, capitulos: [{numero, titulo,
     secciones: [{numero, bloques: [...]}]}]}]}
"""
import html
import io
import os
import re
import unicodedata
import zipfile
from datetime import datetime, timezone

LICENCIA = "Creative Commons BY-SA 4.0"
EDITORIAL = "Tinta y Datos"
IDIOMA = "es"

CSS = """\
@charset "utf-8";
html { font-size: 100%; }
body { margin: 0 5%; line-height: 1.5; text-align: justify;
       hyphens: auto; -webkit-hyphens: auto; }
h1, h2, h3 { text-align: left; line-height: 1.25; font-weight: normal;
             page-break-after: avoid; break-after: avoid; }
h1 { font-size: 1.35em; margin: 1.6em 0 0.9em; }
.portada h1 { font-size: 1.8em; margin: 0 0 0.6em; }
h2 { font-size: 1.3em; margin: 1.6em 0 0.8em; }
h3 { font-size: 1.1em; margin: 1.4em 0 0.6em; }
p { margin: 0; text-indent: 1.2em; }
p.primero, h1 + p, h2 + p, h3 + p, hr + p { text-indent: 0; }
p.verso { text-indent: 0; margin: 0 0 0 1em; text-align: left;
          white-space: normal; }
.seccion { text-align: center; margin: 1.4em 0; border: 0; }
.cubierta { width: 100%; max-width: 100%; height: auto; }
.portada { text-align: center; margin-top: 20%; }
.portada .autor { font-size: 1.1em; margin-top: 1em; }
.colofon { font-size: 0.9em; margin-top: 3em; }
.colofon p { text-indent: 0; margin-bottom: 0.8em; }
nav[epub|type~='toc'] ol { list-style: none; padding-left: 1em; }
"""


def _slug(texto):
    t = unicodedata.normalize("NFKD", str(texto))
    t = t.encode("ascii", "ignore").decode()
    t = re.sub(r"[^\w\s-]", "", t).strip().lower()
    return re.sub(r"[-\s]+", "-", t) or "seccion"


def _esc(t):
    return html.escape(str(t), quote=False)


def _bloque_html(bloque):
    """Un bloque puede ser texto, una lista de versos o un dict con ambos."""
    if isinstance(bloque, dict):
        texto = bloque.get("texto") or bloque.get("lineas") or ""
        es_verso = bloque.get("voz") == "verso" or isinstance(texto, (list, tuple))
    else:
        texto = bloque
        es_verso = isinstance(bloque, (list, tuple))

    if isinstance(texto, (list, tuple)):
        lineas = [_esc(l) for l in texto if str(l).strip()]
        if not lineas:
            return ""
        cuerpo = "<br/>\n      ".join(lineas)
        return f'    <p class="verso">{cuerpo}</p>'
    texto = _esc(texto).strip()
    return f"    <p>{texto}</p>" if texto else ""


def _titulo_capitulo(cap):
    num, tit = cap.get("numero"), cap.get("titulo")
    if num and tit:
        return f"{num}. {tit}"
    return str(tit or num or "").strip()


def _xhtml(titulo_doc, cuerpo, tipo_epub=None):
    attr = f' epub:type="{tipo_epub}"' if tipo_epub else ""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops" lang="{IDIOMA}" xml:lang="{IDIOMA}">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(titulo_doc)}</title>
  <link rel="stylesheet" type="text/css" href="estilo.css"/>
</head>
<body>
  <section{attr}>
{cuerpo}
  </section>
</body>
</html>
"""


def _documentos(obra, con_cubierta=False):
    """Devuelve [(nombre_archivo, titulo_para_indice, xhtml, nivel)]."""
    docs = []
    titulo, autor = obra.get("titulo", ""), obra.get("autor", "")

    if con_cubierta:
        cuerpo = ('    <img src="cubierta.png" alt="Cubierta de '
                  f'{_esc(titulo)}, de {_esc(autor)}" class="cubierta"/>')
        docs.append(("cubierta.xhtml", None, _xhtml(titulo, cuerpo, "cover"), None))

    # Portada
    cuerpo = (f'    <div class="portada">\n'
              f'      <h1>{_esc(titulo)}</h1>\n'
              f'      <p class="autor">{_esc(autor)}</p>\n'
              f'    </div>')
    docs.append(("portada.xhtml", titulo, _xhtml(titulo, cuerpo, "titlepage"), None))

    n = 0
    for parte in obra.get("partes", []):
        nombre_parte = parte.get("nombre")
        if nombre_parte:
            n += 1
            cuerpo = f"    <h1>{_esc(nombre_parte)}</h1>"
            docs.append((f"p{n:03d}-{_slug(nombre_parte)}.xhtml", nombre_parte,
                         _xhtml(nombre_parte, cuerpo, "part"), 1))

        for cap in parte.get("capitulos", []):
            n += 1
            tit_cap = _titulo_capitulo(cap)
            piezas = [f"    <h1>{_esc(tit_cap)}</h1>"] if tit_cap else []
            for i, sec in enumerate(cap.get("secciones", [])):
                num_sec = sec.get("numero")
                if num_sec not in (None, ""):
                    piezas.append(f'    <h2>{_esc(num_sec)}</h2>')
                elif i > 0:
                    piezas.append('    <hr class="seccion"/>')
                for bloque in sec.get("bloques", []):
                    trozo = _bloque_html(bloque)
                    if trozo:
                        piezas.append(trozo)
            docs.append((f"c{n:03d}-{_slug(tit_cap or n)}.xhtml",
                         tit_cap or f"Sección {n}",
                         _xhtml(tit_cap or titulo, "\n".join(piezas), "chapter"),
                         2 if nombre_parte else 1))

    # Colofón al final: en lectores digitales lo habitual es abrir en el texto.
    # Queda enlazado desde el índice, así que sigue siendo accesible al inicio.
    fuente = obra.get("fuente") or {}
    partes_col = ["    <h1>Sobre esta edición</h1>"]
    if isinstance(fuente, dict) and fuente.get("texto"):
        partes_col.append(f"    <p>Texto base: {_esc(fuente['texto'])}</p>")
        if fuente.get("nota"):
            partes_col.append(f"    <p>{_esc(fuente['nota'])}</p>")
    partes_col += [
        f"    <p>Obra en dominio público. Edición digital de {EDITORIAL}.</p>",
        f"    <p>La composición, el diseño y la cubierta de esta edición se "
        f"publican bajo licencia {LICENCIA}: puedes reutilizarlos y "
        f"redistribuirlos citando la autoría y manteniendo la misma licencia.</p>",
    ]
    docs.append(("colofon.xhtml", "Sobre esta edición",
                 _xhtml("Sobre esta edición",
                        '<div class="colofon">\n' + "\n".join(partes_col) + "\n</div>",
                        "colophon"), None))
    return docs


def _nav(docs, titulo):
    items = "\n".join(
        f'      <li><a href="{n}">{_esc(t)}</a></li>'
        for n, t, _, nivel in docs if nivel is not None or n == "colofon.xhtml")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:epub="http://www.idpf.org/2007/ops" lang="{IDIOMA}" xml:lang="{IDIOMA}">
<head>
  <meta charset="utf-8"/>
  <title>Índice</title>
  <link rel="stylesheet" type="text/css" href="estilo.css"/>
</head>
<body>
  <nav epub:type="toc" id="toc" role="doc-toc">
    <h1>Índice</h1>
    <ol>
{items}
    </ol>
  </nav>
</body>
</html>
"""


def _opf(obra, docs, ident, con_cubierta=False):
    titulo, autor = obra.get("titulo", ""), obra.get("autor", "")
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = ['    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
                '    <item id="css" href="estilo.css" media-type="text/css"/>']
    if con_cubierta:
        manifest.append('    <item id="cover-image" href="cubierta.png" '
                        'media-type="image/png" properties="cover-image"/>')
    spine = []
    for i, (nombre, _t, _c, _n) in enumerate(docs):
        idx = f"d{i:03d}"
        manifest.append(f'    <item id="{idx}" href="{nombre}" media-type="application/xhtml+xml"/>')
        spine.append(f'    <itemref idref="{idx}"/>')
    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0"
         unique-identifier="pub-id" xml:lang="{IDIOMA}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="pub-id">{_esc(ident)}</dc:identifier>
    <dc:title>{_esc(titulo)}</dc:title>
    <dc:creator>{_esc(autor)}</dc:creator>
    <dc:language>{IDIOMA}</dc:language>
    <dc:publisher>{EDITORIAL}</dc:publisher>
    <dc:rights>Obra en dominio público. Composición y diseño bajo {LICENCIA}.</dc:rights>
    <meta property="dcterms:modified">{ahora}</meta>
    <meta property="schema:accessMode">textual</meta>
    <meta property="schema:accessModeSufficient">textual</meta>
    <meta property="schema:accessibilityFeature">structuralNavigation</meta>
    <meta property="schema:accessibilityFeature">tableOfContents</meta>
    <meta property="schema:accessibilityFeature">readingOrder</meta>
    <meta property="schema:accessibilityHazard">none</meta>
    <meta property="schema:accessibilitySummary">Publicación totalmente textual, con navegación por capítulos y sin contenido que dependa de imágenes o color.</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest)}
  </manifest>
  <spine>
{chr(10).join(spine[:1])}
    <itemref idref="nav"/>
{chr(10).join(spine[1:])}
  </spine>
</package>
"""


CONTAINER = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def generar(obra, salida, identificador=None, dominio=None):
    """Genera un EPUB 3. Devuelve la ruta.

    Si `dominio` viene informado, añade una cubierta tipográfica con el color
    de ese dominio. Sin cubierta.py disponible, el EPUB se genera igual.
    """
    png = None
    if dominio:
        try:
            import cubierta
            buf = io.BytesIO()
            cubierta.generar(obra, buf, dominio=dominio)
            png = buf.getvalue()
        except Exception as e:
            print(f"  Aviso: sin cubierta ({e})")
    docs = _documentos(obra, con_cubierta=png is not None)
    ident = identificador or f"urn:tintaydatos:{_slug(obra.get('titulo', 'obra'))}"
    carpeta = os.path.dirname(salida)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    with zipfile.ZipFile(salida, "w") as z:
        # mimetype: primero y sin comprimir, lo exige la especificación
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip",
                   compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", CONTAINER, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", _opf(obra, docs, ident, png is not None),
                   zipfile.ZIP_DEFLATED)
        if png:
            z.writestr("OEBPS/cubierta.png", png, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", _nav(docs, obra.get("titulo", "")), zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/estilo.css", CSS, zipfile.ZIP_DEFLATED)
        for nombre, _t, contenido, _n in docs:
            z.writestr(f"OEBPS/{nombre}", contenido, zipfile.ZIP_DEFLATED)

    print(f"Generado: {salida}")
    return salida
