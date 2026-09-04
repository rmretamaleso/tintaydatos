"""
Generador de ediciones PDF de Tinta y Datos. Reemplaza a generar_edicion.py y
generar_edicion_verso.py: maneja prosa y verso con la misma estructura.

Recibe un ÁRBOL (dict), no texto. Quien lo produzca es problema de otro módulo.

    {
      "titulo": "...", "autor": "...", "anio": 1887,
      "tipo": "prosa" | "verso",
      "fuente": {"texto": "...", "url": "...", "nota": "..."},
      "catalogo": "un catálogo de literatura en español en dominio público",
      "partes": [
        {"nombre": "Parte 1" | None,
         "capitulos": [
           {"numero": "1" | "I" | None,
            "titulo": "Juanito Santa Cruz" | None,
            "secciones": [
              {"numero": "1" | None,
               "bloques": [...]}      # prosa: ["párrafo", ...]
            ]}                        # verso: [["verso", "verso"], ...]
        ]}
      ]
    }

Un verso o párrafo que empiece por ">> " se compone como acotación (voces, etc.).
"""
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, Table,
                                TableStyle,
                                SimpleDocTemplate, Spacer)

TINTA = colors.HexColor('#1C2B4A')
TINTA_CLARA = colors.HexColor('#3d4f74')
MALVA = colors.HexColor('#6B4C8C')

CATALOGO_POR_DEFECTO = "un catálogo de literatura en español en dominio público"


def _resolver_idioma(lang):
    """Acepta 'es' aunque el diccionario instalado se llame 'es_ES', y al revés."""
    try:
        import pyphen
    except ImportError:
        raise SystemExit(
            "La opción 'hyphenation' necesita pyphen y no está instalado.\n"
            "  pip install pyphen --break-system-packages\n"
            "Si prefieres seguir sin partición, quita \"hyphenation\" del .json.")

    disponibles = sorted(pyphen.LANGUAGES)
    if lang in disponibles:
        return lang
    raiz = lang.split("_")[0].lower()
    cerca = [l for l in disponibles if l.split("_")[0].lower() == raiz]
    if cerca:
        print(f"  (uso el diccionario «{cerca[0]}» para «{lang}»)")
        return cerca[0]

    raise SystemExit(
        f"pyphen no tiene ningún diccionario para «{lang}».\n"
        f"Diccionarios instalados: {len(disponibles)}"
        + (f" ({', '.join(disponibles[:10])}…)" if disponibles else "")
        + "\n\nEl paquete de Ubuntu python3-pyphen viene sin diccionarios; los espera\n"
          "del sistema. Dos salidas:\n"
          "  sudo apt install hyphen-es\n"
          "  pip install --upgrade --ignore-installed pyphen --break-system-packages\n"
          "La segunda instala la versión de PyPI, que trae 85 diccionarios incluidos.\n"
          "O quita \"hyphenation\" del .json para generar sin partición.")


def _estilos(hyphenation=None):
    s = getSampleStyleSheet()
    extra = {"hyphenationLang": _resolver_idioma(hyphenation)} if hyphenation else {}
    return {
        "titulo": ParagraphStyle('T', parent=s['Title'], fontName='Times-Bold',
            fontSize=22, leading=26, alignment=TA_CENTER, spaceAfter=14, textColor=TINTA),
        "autor": ParagraphStyle('A', parent=s['Normal'], fontName='Times-Italic',
            fontSize=14, alignment=TA_CENTER, textColor=TINTA_CLARA, spaceAfter=6),
        "fechas_autor": ParagraphStyle('FA', parent=s['Normal'],
            fontName='Times-Roman', fontSize=10, alignment=TA_CENTER,
            textColor=TINTA_CLARA, spaceAfter=10),
        "anio": ParagraphStyle('Y', parent=s['Normal'], fontName='Times-Italic',
            fontSize=11, alignment=TA_CENTER, textColor=TINTA_CLARA),
        "sello": ParagraphStyle('S', parent=s['Normal'], fontName='Courier',
            fontSize=9, alignment=TA_CENTER, textColor=MALVA, spaceBefore=40),
        "colofon": ParagraphStyle('C', parent=s['Normal'], fontName='Times-Roman',
            fontSize=9.5, leading=13, alignment=TA_LEFT, textColor=TINTA_CLARA),
        "parte": ParagraphStyle('P', parent=s['Title'], fontName='Times-Bold',
            fontSize=18, alignment=TA_CENTER, textColor=TINTA,
            spaceBefore=100, spaceAfter=30),
        "capitulo": ParagraphStyle('K', parent=s['Heading1'], fontName='Times-Bold',
            fontSize=13, alignment=TA_CENTER, textColor=MALVA,
            spaceBefore=18, spaceAfter=6),
        "captitulo": ParagraphStyle('KT', parent=s['Normal'], fontName='Times-Italic',
            fontSize=11, leading=14, alignment=TA_CENTER, textColor=TINTA_CLARA,
            spaceAfter=14),
        "seccion": ParagraphStyle('N', parent=s['Normal'], fontName='Times-Bold',
            fontSize=10, alignment=TA_CENTER, textColor=MALVA,
            spaceBefore=12, spaceAfter=8),
        "parrafo": ParagraphStyle('Pr', parent=s['Normal'], fontName='Times-Roman',
            fontSize=11, leading=15.5, alignment=TA_JUSTIFY,
            firstLineIndent=14, spaceAfter=6, **extra),
        "indice": ParagraphStyle('Ix', parent=s['Normal'], fontName='Times-Roman',
            fontSize=10.5, leading=15, alignment=TA_LEFT, leftIndent=18,
            firstLineIndent=-12, spaceAfter=2, textColor=TINTA),
        "cita": ParagraphStyle('Ci', parent=s['Normal'], fontName='Times-Roman',
            fontSize=10, leading=14, alignment=TA_LEFT, leftIndent=30,
            firstLineIndent=0, spaceAfter=0),
        "verso": ParagraphStyle('V', parent=s['Normal'], fontName='Times-Roman',
            fontSize=10.5, leading=15, alignment=TA_LEFT, spaceAfter=0),
        "acotacion": ParagraphStyle('Ac', parent=s['Normal'], fontName='Times-Bold',
            fontSize=9.5, alignment=TA_CENTER, textColor=MALVA,
            spaceBefore=6, spaceAfter=6),
    }


_RESPALDO = None
_CANDIDATAS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _fuente_respaldo():
    """Registra, una sola vez, una fuente con cobertura amplia."""
    global _RESPALDO
    if _RESPALDO is None:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        _RESPALDO = ""
        for ruta in _CANDIDATAS:
            if os.path.exists(ruta):
                pdfmetrics.registerFont(TTFont("Respaldo", ruta))
                _RESPALDO = "Respaldo"
                break
    return _RESPALDO or None


def _esc(t):
    """Escapa el marcado y sustituye la fuente donde Times no llega.

    Los tipos base de reportlab solo cubren el juego latino (WinAnsi): un
    texto en griego, cirílico o con símbolos raros saldría en blanco, y la
    verificación lo detectaría como texto ausente. Aquí esos tramos se marcan
    con una fuente de respaldo, sin tocar el resto de la composición.
    """
    t = t.replace("&", "&amp;").replace("<", "&lt;")
    if all(_cabe(c) for c in t):
        return t
    respaldo = _fuente_respaldo()
    if not respaldo:
        raise SystemExit(
            "El texto tiene caracteres fuera del juego latino y no encontré una "
            "fuente de respaldo.\n  sudo apt install fonts-dejavu-core")
    salida, buf, fuera = [], [], False
    for c in t:
        if _cabe(c) == (not fuera):
            buf.append(c); continue
        salida.append(_tramo("".join(buf), fuera, respaldo))
        buf, fuera = [c], not fuera
    salida.append(_tramo("".join(buf), fuera, respaldo))
    return "".join(salida)


def _cabe(c):
    try:
        c.encode("cp1252")
        return True
    except UnicodeEncodeError:
        return False


def _tramo(texto, fuera, respaldo):
    if not texto:
        return ""
    return f'<font name="{respaldo}">{texto}</font>' if fuera else texto


def _portada(obra, est, subtitulo=None):
    fs = [Spacer(1, 4 * cm), Paragraph(_esc(obra["titulo"]), est["titulo"])]
    if subtitulo:
        fs.append(Paragraph(_esc(subtitulo), est["autor"]))
    # Las fechas del autor van bajo su nombre: son un dato objetivo, y dejan al
    # lector calcular el plazo de dominio público según la ley de su país, que
    # varía —70 años en casi toda América, 80 en España para algunos autores.
    autor = _esc(obra["autor"])
    fechas = obra.get("fechas_autor")
    fs.append(Paragraph(autor, est["autor"]))
    if fechas:
        fs.append(Paragraph(_esc(fechas), est["fechas_autor"]))
    if obra.get("anio"):
        fs.append(Paragraph(str(obra["anio"]), est["anio"]))
    fs.append(Paragraph("TINTA Y DATOS — CATÁLOGO SEMILLA", est["sello"]))
    fs.append(PageBreak())
    return fs


def _colofon(obra, est):
    f = obra.get("fuente", {})
    # El año de la edición se guarda en el .json la primera vez que se publica,
    # así que una obra regenerada más adelante conserva la fecha en que
    # realmente se hizo, no la del día que se vuelve a componer.
    hecha = obra.get("anio_edicion")
    en_anio = f" en {hecha}" if hecha else ""
    t = (f"Esta es una edición propia de <b>Tinta y Datos</b> (tintaydatos.com), "
         f"{obra.get('catalogo', CATALOGO_POR_DEFECTO)}. El texto de esta obra está "
         f"verificado como libre de derechos de autor. "
         f"Texto cotejado contra: {f.get('texto','—')} ({f.get('url','—')}). "
         f"Esta edición fue tipografiada de nuevo por Tinta y Datos{en_anio} — no es "
         f"una copia del archivo de la fuente original, solo del texto, que es de "
         f"dominio público.")
    if f.get("nota"):
        t += " " + f["nota"]
    return [Paragraph(t, est["colofon"]), PageBreak()]


def _bloques(bloques, tipo, est, umbral):
    """Devuelve los flowables de una sección."""
    fs = []
    if tipo == "verso":
        for estrofa in bloques:
            # Una obra en verso puede traer bloques en prosa (portadillas,
            # dedicatorias, argumentos). Sin esto se recorrerían carácter a
            # carácter y cada letra saldría como un verso.
            if isinstance(estrofa, str):
                if estrofa.strip():
                    fs.append(Paragraph(_esc(estrofa), est["parrafo"]))
                continue
            grupo = []
            for v in estrofa:
                if v.startswith(">> "):
                    grupo.append(Paragraph(_esc(v[3:]), est["acotacion"]))
                else:
                    grupo.append(Paragraph(_esc(v), est["verso"]))
            grupo.append(Spacer(1, 10))
            fs.append(KeepTogether(grupo) if len(estrofa) <= umbral else grupo)
    else:
        for p in bloques:
            # Un bloque de varias líneas dentro de prosa es una cita en verso
            # (o una dedicatoria): hay que conservar los saltos, no unirlos.
            if isinstance(p, list):
                grupo = [Paragraph(_esc(l), est["cita"]) for l in p if l.strip()]
                if grupo:
                    fs.append(KeepTogether([Spacer(1, 6)] + grupo + [Spacer(1, 8)]))
                continue
            if not p.strip():
                continue
            if p.startswith(">> "):
                fs.append(Paragraph(_esc(p[3:]), est["acotacion"]))
            else:
                fs.append(Paragraph(_esc(p), est["parrafo"]))
    return [f for sub in fs for f in (sub if isinstance(sub, list) else [sub])]


def _cuerpo(partes, obra, est, opciones):
    tipo = obra.get("tipo", "prosa")
    salto_cap = opciones.get("salto_por_capitulo", tipo == "prosa")
    umbral = opciones.get("umbral_estrofa_entera", 12)
    etiq = opciones.get("etiqueta_capitulo", "")

    story = []
    for i, parte in enumerate(partes):
        if parte.get("nombre"):
            if story:
                story.append(PageBreak())
            story.append(Paragraph(_esc(parte["nombre"]), est["parte"]))
            story.append(PageBreak())

        for j, cap in enumerate(parte["capitulos"]):
            if salto_cap and story and not (parte.get("nombre") and j == 0):
                story.append(PageBreak())

            enc = []
            if cap.get("numero") is not None:
                num = str(cap["numero"])
                # La etiqueta ("CAPÍTULO", "RIMA"…) solo tiene sentido delante de
                # un número. Un encabezado con título propio va tal cual.
                numerado = bool(re.fullmatch(r"\d+|[IVXLCDM]+", num))
                titulo = f"{etiq} {num}" if (etiq and numerado) else num
                enc.append(Paragraph(_esc(titulo), est["capitulo"]))
            if cap.get("titulo"):
                enc.append(Paragraph(_esc(cap["titulo"]), est["captitulo"]))

            secs = cap["secciones"]
            if not secs:
                # Encabezado que solo introduce a los siguientes, sin texto propio
                if enc:
                    story.append(KeepTogether(enc))
                continue
            primeros = _bloques(secs[0]["bloques"], tipo, est, umbral)
            if secs[0].get("numero") is not None:
                primeros = [Paragraph(str(secs[0]["numero"]), est["seccion"])] + primeros
            # el encabezado nunca queda huérfano al pie de página
            if enc:
                story.append(KeepTogether(enc + primeros[:2]))
                story.extend(primeros[2:])
            else:
                story.extend(primeros)

            for sec in secs[1:]:
                if sec.get("numero") is not None:
                    story.append(Paragraph(str(sec["numero"]), est["seccion"]))
                story.extend(_bloques(sec["bloques"], tipo, est, umbral))
    return story


OPCIONES_VALIDAS = {"etiqueta_capitulo", "salto_por_capitulo",
                    "umbral_estrofa_entera", "hyphenation", "subtitulo",
                    "indice"}


def piezas_independientes(partes, forzar=None):
    """Títulos que corresponden a textos con vida propia, no a capítulos.

    `forzar` permite que el .json decida cuando la forma no basta: «1. El rapto
    del sol» (cuento de Sub Sole) y «I. Santa María de la Ladrillera» (capítulo
    de Los bandidos de Río Frío) son indistinguibles por su forma, y solo quien
    conoce la obra sabe cuál es cuál.

    Sirve para el catálogo y el buscador: interesa que alguien encuentre «El
    fardo» dentro de «Azul», no que se listen los 137 capítulos del Quijote.
    Un cuento se titula «El fardo»; un capítulo de novela, «Que trata de la
    condición y ejercicio del famoso hidalgo». El largo los separa, y la
    palabra «capítulo» al principio lo confirma.
    """
    titulos = piezas_con_titulo(partes)
    if not titulos or forzar is False:
        return []
    if forzar is True:
        return titulos
    capitulados = sum(1 for t in titulos
                      if re.match(r"(cap[íi]tulo|canto|jornada|acto|libro|parte)\b"
                                  r"|^[IVXLCDM]+\s*[.\-—]"      # «I. Santa María…»
                                  r"|^\d+\s*[.\-—]",            # «1. El rapto del sol»
                                  t.strip(), re.I))
    if capitulados > len(titulos) / 3:
        return []
    medio = sum(len(t) for t in titulos) / len(titulos)
    return [] if medio > 40 else titulos


def piezas_con_titulo(partes):
    """Títulos de los capítulos, si la obra es una colección de piezas nombradas.

    Un índice tiene sentido en un libro de cuentos o poemas, donde cada pieza
    se busca por su nombre. En una novela con capítulos I a XXX sería una lista
    de números: por eso solo se considera cuando los encabezados no son meros
    numerales.
    """
    titulos = [str(c["numero"]) for p in partes for c in p["capitulos"]
               if c.get("numero") is not None]
    if len(titulos) < 3:
        return []
    numerales = sum(1 for t in titulos
                    if re.fullmatch(r"\d+|[IVXLCDM]+|\d+\.?\s*", t.strip()))
    return [] if numerales > len(titulos) / 2 else titulos


def _indice(titulos, est, por_bloque=30):
    """Índice a dos columnas, troceado en tablas que sí pueden partirse.

    Una tabla de reportlab no se divide entre páginas si sus filas son altas:
    con títulos largos la tabla supera la caja y la composición falla. Se arma
    entonces en bloques, cada uno con su tabla.

    Y si los «títulos» son en realidad sumarios de capítulo —«I. Lunes Santo.
    —Descansamos en Albuñol.—Cosas de la Luna…»— no se hace índice: una sola
    entrada ocuparía varias páginas y no sería un índice sino otro texto.
    """
    if not titulos:
        return []
    if max(len(t) for t in titulos) > 120:
        return []
    fs = [Paragraph("ÍNDICE", est["capitulo"]), Spacer(1, 12)]
    for inicio in range(0, len(titulos), por_bloque):
        trozo = titulos[inicio:inicio + por_bloque]
        mitad = (len(trozo) + 1) // 2
        filas = []
        for i in range(mitad):
            izq = Paragraph(_esc(trozo[i]), est["indice"])
            der = (Paragraph(_esc(trozo[i + mitad]), est["indice"])
                   if i + mitad < len(trozo) else "")
            filas.append([izq, der])
        tabla = Table(filas, colWidths=[6.1 * cm, 6.1 * cm])
        tabla.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        fs.append(tabla)
    fs.append(PageBreak())
    return fs


def generar(obra, salida, **opciones):
    """Genera un PDF. Devuelve la ruta."""
    desconocidas = set(opciones) - OPCIONES_VALIDAS
    if desconocidas:
        raise ValueError(f"Opciones desconocidas: {sorted(desconocidas)}. "
                         f"Válidas: {sorted(OPCIONES_VALIDAS)}")
    est = _estilos(opciones.get("hyphenation"))
    doc = SimpleDocTemplate(salida, pagesize=A5,
                            topMargin=2.2 * cm, bottomMargin=2.2 * cm,
                            leftMargin=2.2 * cm, rightMargin=2 * cm,
                            title=obra["titulo"], author=obra["autor"])
    story = _portada(obra, est, opciones.get("subtitulo"))
    story += _colofon(obra, est)
    if opciones.get("indice", True):
        story += _indice(piezas_con_titulo(obra["partes"]), est)
    story += _cuerpo(obra["partes"], obra, est, opciones)
    doc.build(story)
    print(f"Generado: {salida}")
    return salida


def generar_por_parte(obra, patron_salida, **opciones):
    """Un PDF por parte. patron_salida usa {n} y {slug}: 'fyj-parte-{n}.pdf'."""
    salidas = []
    for n, parte in enumerate(obra["partes"], 1):
        sub = dict(obra)
        sub["partes"] = [{"nombre": None, "capitulos": parte["capitulos"]}]
        salida = patron_salida.format(n=n)
        salidas.append(generar(sub, salida,
                               subtitulo=parte.get("nombre"), **opciones))
    return salidas
