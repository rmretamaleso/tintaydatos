"""
Lee obras de Project Gutenberg y las entrega como HTML para el parser común.

Gutenberg es la fuente con mejor procedencia de las que usamos: su cabecera
declara de qué edición impresa proviene el texto, quién lo transcribió y qué
biblioteca aportó las imágenes. Nada de eso lo dicen textos.info ni Wikisource.

El texto viene envuelto en la cabecera y el pie legal de Gutenberg, delimitados
por marcas «*** START OF ...» y «*** END OF ...». Se recortan: no son parte de
la obra, y su licencia permite retirar esas referencias cuando la redistribución
es gratuita. El colofón cita la edición original y a los transcriptores.
"""
import json
import re
import time

API = "https://gutendex.com/books"
AGENTE = {"User-Agent": "TintaYDatos/1.0"}


def _pedir(url, intentos=4, espera=120):
    try:
        import requests
    except ImportError:
        raise SystemExit("Falta requests:  pip install requests --break-system-packages")
    ultimo = ""
    for n in range(intentos):
        try:
            r = requests.get(url, timeout=espera, headers=AGENTE)
        except Exception as e:
            ultimo = type(e).__name__
            time.sleep(3 * (n + 1))
            continue
        if r.status_code == 404:
            raise RuntimeError(f"Gutenberg no tiene {url}")
        if r.status_code != 200:
            ultimo = f"HTTP {r.status_code}"
            time.sleep(3 * (n + 1))
            continue
        return r.text
    raise RuntimeError(f"No pude descargar {url} ({ultimo}).")


def ficha(libro_id):
    """Datos del libro: título, autor, edición original y transcriptores."""
    d = json.loads(_pedir(f"{API}/{libro_id}"))
    crudo = _pedir(f"https://www.gutenberg.org/ebooks/{libro_id}.txt.utf-8")
    cab = crudo[:crudo.find("*** START OF")] if "*** START OF" in crudo else crudo[:2000]

    def campo(nombre):
        m = re.search(rf"^{nombre}:\s*(.+)$", cab, re.M)
        return m.group(1).strip() if m else ""

    # Los créditos traen la URL de pgdp.net y notas entre paréntesis sobre la
    # digitalización; en el colofón estorban y el enlace ya va aparte.
    creditos = campo("Credits")
    limpio = re.sub(r"\s*\(.*?\)\s*$", "", creditos)
    limpio = re.sub(r"\s+at\s+https?://\S+", "", limpio)
    limpio = re.sub(r"https?://\S+", "", limpio).strip(" .,")

    return {
        "id": libro_id,
        "titulo": d.get("title", "").strip(),
        "autores": [a["name"] for a in d.get("authors", [])],
        "edicion_original": campo("Original publication"),
        "transcriptores": limpio,
        "creditos_completos": creditos,
    }


def descargar_html(libro_id):
    """HTML de la obra, ya sin la cabecera ni el pie legal de Gutenberg."""
    h = _pedir(f"https://www.gutenberg.org/ebooks/{libro_id}.html.images")

    # El contenido va entre las marcas de inicio y fin. En la versión HTML
    # aparecen dentro de secciones con id pg-header y pg-footer.
    for patron in (r'<section[^>]*id="pg-header".*?</section>',
                   r'<section[^>]*id="pg-footer".*?</section>',
                   r'<div[^>]*id="pg-header".*?</div>\s*(?=<)',
                   r'<div[^>]*id="pg-footer".*?</div>\s*(?=<)'):
        h = re.sub(patron, "", h, flags=re.S | re.I)

    # Por si el HTML usa las marcas de texto plano en vez de secciones
    m = re.search(r"\*\*\*\s*START OF TH[EI]S? PROJECT GUTENBERG.*?\*\*\*", h, re.I)
    if m:
        h = h[m.end():]
    m = re.search(r"\*\*\*\s*END OF TH[EI]S? PROJECT GUTENBERG.*?\*\*\*", h, re.I)
    if m:
        h = h[:m.start()]

    # El parser común busca el contenido dentro de <article>; se lo damos.
    cuerpo = re.search(r"<body[^>]*>(.*)</body>", h, re.S | re.I)
    dentro = cuerpo.group(1) if cuerpo else h

    # El <h1> de Gutenberg es el título de la obra, que ya va en la portada.
    dentro = re.sub(r"<h1\b[^>]*>.*?</h1>", "", dentro, flags=re.S | re.I)

    # Muchas ediciones traen su propio índice, que duplicaría el que compone
    # Tinta y Datos. Se descarta junto con la lista que lo sigue.
    dentro = re.sub(r"<h[2-3]\b[^>]*>\s*(ÍNDICE|INDICE|Índice|Indice)\s*\.?\s*"
                    r"</h[2-3]>.*?(?=<h[1-3]\b)", "", dentro, flags=re.S)

    # Las notas del transcriptor hablan del libro electrónico, no de la obra.
    # Gutenberg las envuelve en un div de clase «tnotes», así que se descarta
    # el bloque entero; el rótulo va dentro de <strong> y no siempre en un <p>.
    dentro = re.sub(r'<div[^>]*class="[^"]*tnotes[^"]*"[^>]*>.*?</div>\s*</div>',
                    "", dentro, flags=re.S | re.I)
    dentro = re.sub(r'<div[^>]*class="[^"]*tnotes[^"]*"[^>]*>.*?</div>',
                    "", dentro, flags=re.S | re.I)
    # Y por si aparece suelta, sin el div que la envuelve
    dentro = re.sub(
        r"<p[^>]*>\s*(?:<(?:strong|b)>)?\s*"
        r"(?:Nota del transcriptor|Transcriber'?s? Note)\s*:?\s*"
        r"(?:</(?:strong|b)>)?\s*</p>"
        r"(\s*<p[^>]*>(?:(?!</p>).)*?"
        r"(?:libro electr[óo]nico|ebook|dominio p[úu]blico|public domain)"
        r"(?:(?!</p>).)*?</p>)*",
        "", dentro, flags=re.S | re.I)
    return f"<article>{dentro}</article>"


def colofon(f):
    """Frase de procedencia para el .json de la obra.

    Cita la edición impresa de origen y a quienes la transcribieron, que es lo
    que la licencia de Gutenberg pide reconocer cuando se retira su marca.
    """
    partes = []
    if f.get("transcriptores"):
        partes.append(f"transcripción de {f['transcriptores']}")
    if f.get("edicion_original"):
        partes.append(f"a partir de la edición de {f['edicion_original']}")
    detalle = ", ".join(partes)
    return f"Project Gutenberg ({detalle})" if detalle else "Project Gutenberg"
