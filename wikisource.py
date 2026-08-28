"""
Lee obras de Wikisource y las entrega como árbol para edicion.py.

Wikisource es la mejor fuente que hemos evaluado en cuanto a procedencia: cada
texto se transcribe página por página contra un facsímil concreto y queda
marcado como validado cuando dos personas distintas lo cotejaron. A cambio, la
obra vive repartida en muchas páginas del wiki.

El exportador oficial (ws-export) resuelve ese armado y entrega un ePub con un
archivo XHTML por pieza, en orden. De ahí sale el texto, con la ventaja de que
Wikisource marca estrofas y versos de forma explícita.
"""
import html as _entidades
import io
import re
import sys
import time
import zipfile

EXPORT = "https://ws-export.wmcloud.org/"
API = "https://es.wikisource.org/w/api.php"
OMITIR = ("nav.xhtml", "title.xhtml", "about.xhtml", "cover.xhtml")


def descargar_epub(pagina, lang="es", intentos=3, espera=120):
    """El exportador rechaza algunos clientes; conviene identificarse."""
    try:
        import requests
    except ImportError:
        sys.exit("Falta requests:  pip install requests --break-system-packages")
    ultimo = ""
    for n in range(intentos):
        try:
            r = requests.get(EXPORT, timeout=espera,
                             params={"lang": lang, "format": "epub",
                                     "page": pagina.replace(" ", "_")},
                             headers={"User-Agent": "TintaYDatos/1.0"})
        except Exception as e:
            ultimo = type(e).__name__
            time.sleep(3 * (n + 1)); continue
        if r.status_code == 404:
            raise RuntimeError(f"Wikisource no tiene la página «{pagina}».")
        if r.status_code != 200 or r.content[:4] != b"PK\x03\x04":
            ultimo = f"HTTP {r.status_code}"
            time.sleep(3 * (n + 1)); continue
        return r.content
    raise RuntimeError(f"No pude exportar «{pagina}» ({ultimo}).")


def _texto(html):
    html = re.sub(r"<[^>]+>", "", html)
    html = _entidades.unescape(html)
    # el espacio de cuadratín marca la sangría del verso, no es texto
    html = html.replace("\u2003", " ").replace("\u00a0", " ").replace("\u2002", " ")
    return re.sub(r"\s+", " ", html).strip()


def _titulo(doc):
    m = re.search(r'<h[1-6][^>]*class="[^"]*ws-h[^"]*"[^>]*>(.*?)</h[1-6]>', doc, re.S)
    if not m:
        m = re.search(r"<h[1-6][^>]*>(.*?)</h[1-6]>", doc, re.S)
    return _texto(m.group(1)) if m else None


def _decorativo(estrofa):
    """¿Es una portadilla del facsímil compuesta letra por letra?

    Las ediciones de vanguardia traen portadas con el título en vertical, una
    letra por línea. Wikisource las transcribe así y sin esto cada letra
    entraría como un verso: en «Altazor» eran 7.293 de 9.553 líneas.
    """
    if len(estrofa) < 4:
        return False
    sueltas = sum(1 for v in estrofa if len(v.strip()) == 1)
    return sueltas / len(estrofa) >= 0.7


def _bloques(doc):
    """Devuelve (tipo, bloques). Verso si la pieza trae marcas de poema."""
    estrofas, descartadas = [], 0
    for est in re.findall(r'<div class="[^"]*ws-poema-estrofa[^"]*".*?>(.*?)</div>',
                          doc, re.S):
        versos = [_texto(v) for v in
                  re.findall(r'<span class="ws-poema-line">(.*?)</span>\s*(?=<span class="ws-poema-line">|$)',
                             est, re.S)]
        versos = [v for v in versos if v]
        if not versos:
            continue
        if _decorativo(versos):
            descartadas += len(versos)
            continue
        estrofas.append(versos)
    if estrofas:
        return "verso", estrofas, descartadas

    parrafos = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", doc, re.S):
        t = _texto(p)
        if t:
            parrafos.append(t)
    return "prosa", parrafos, descartadas


def arbol(pagina, lang="es"):
    """Devuelve (partes, tipo_predominante) listo para edicion.generar."""
    z = zipfile.ZipFile(io.BytesIO(descargar_epub(pagina, lang)))
    nombres = [n for n in z.namelist()
               if n.endswith((".xhtml", ".html"))
               and not any(n.endswith(o) for o in OMITIR)]
    nombres.sort(key=lambda n: (int(m.group(1)) if (m := re.search(r"/c(\d+)_", n))
                                else 9999, n))
    capitulos, versos, prosa, sueltas = [], 0, 0, 0
    for n in nombres:
        doc = z.read(n).decode("utf-8", "replace")
        cuerpo = doc[doc.find("<body"):]
        tipo, bloques, descartadas = _bloques(cuerpo)
        sueltas += descartadas
        if not bloques:
            continue
        if tipo == "verso":
            versos += sum(len(e) for e in bloques)
        else:
            prosa += len(bloques)
        capitulos.append({"numero": _titulo(cuerpo) or n, "titulo": None,
                          "secciones": [{"numero": None, "bloques": bloques}]})
    if sueltas:
        print(f"  se descartaron {sueltas} líneas de portadillas del facsímil "
              f"compuestas letra por letra")
    if not capitulos:
        raise RuntimeError(f"No reconocí contenido en el ePub de «{pagina}».")
    return [{"nombre": None, "capitulos": capitulos}], ("verso" if versos > prosa
                                                        else "prosa")


ESCALA = [("Textos_validados", "validado"),
          ("Textos_corregidos", "corregido"),
          ("Textos_sin_corregir", "sin corregir")]


def estado_revision(pagina, lang="es", intentos=3):
    """Devuelve 'validado', 'corregido', 'sin corregir' o None si no se pudo saber.

    Wikisource usa una escala de tres niveles: corregido significa que una
    persona cotejó la transcripción contra el facsímil, validado que una
    segunda lo verificó. Un error de consulta devuelve None, nunca un estado
    falso: dar por 'sin corregir' lo que no se pudo comprobar descartaría
    obras publicables.
    """
    import json
    import urllib.parse
    try:
        import requests
    except ImportError:
        return None
    q = urllib.parse.urlencode({"action": "parse", "page": pagina,
                                "prop": "categories", "format": "json",
                                "formatversion": "2"})
    for n in range(intentos):
        try:
            r = requests.get(f"{API}?{q}", timeout=60,
                             headers={"User-Agent": "TintaYDatos/1.0"})
            cats = [c["category"] for c in json.loads(r.text)["parse"]["categories"]]
        except Exception:
            time.sleep(1.5 * (n + 1))
            continue
        for cat, nombre in ESCALA:
            if cat in cats:
                return nombre
        return "sin marca"
    return None


def validado(pagina, lang="es"):
    """Compatibilidad: True solo si está validado."""
    return estado_revision(pagina, lang) == "validado"
