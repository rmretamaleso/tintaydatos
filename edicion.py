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
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph,
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
        "cita": ParagraphStyle('Ci', parent=s['Normal'], fontName='Times-Roman',
            fontSize=10, leading=14, alignment=TA_LEFT, leftIndent=30,
            firstLineIndent=0, spaceAfter=0),
        "verso": ParagraphStyle('V', parent=s['Normal'], fontName='Times-Roman',
            fontSize=10.5, leading=15, alignment=TA_LEFT, spaceAfter=0),
        "acotacion": ParagraphStyle('Ac', parent=s['Normal'], fontName='Times-Bold',
            fontSize=9.5, alignment=TA_CENTER, textColor=MALVA,
            spaceBefore=6, spaceAfter=6),
    }


def _esc(t):
    """reportlab interpreta & y < como marcado; hay que escaparlos."""
    return t.replace("&", "&amp;").replace("<", "&lt;")


def _portada(obra, est, subtitulo=None):
    fs = [Spacer(1, 4 * cm), Paragraph(_esc(obra["titulo"]), est["titulo"])]
    if subtitulo:
        fs.append(Paragraph(_esc(subtitulo), est["autor"]))
    fs.append(Paragraph(_esc(obra["autor"]), est["autor"]))
    if obra.get("anio"):
        fs.append(Paragraph(str(obra["anio"]), est["anio"]))
    fs.append(Paragraph("TINTA Y DATOS — CATÁLOGO SEMILLA", est["sello"]))
    fs.append(PageBreak())
    return fs


def _colofon(obra, est):
    f = obra.get("fuente", {})
    t = (f"Esta es una edición propia de <b>Tinta y Datos</b> (tintaydatos.com), "
         f"{obra.get('catalogo', CATALOGO_POR_DEFECTO)}. El texto de esta obra está "
         f"verificado como libre de derechos de autor. "
         f"Texto cotejado contra: {f.get('texto','—')} ({f.get('url','—')}). "
         f"Esta edición fue tipografiada de nuevo por Tinta y Datos — no es una copia "
         f"del archivo de la fuente original, solo del texto, que es de dominio público.")
    if f.get("nota"):
        t += " " + f["nota"]
    return [Paragraph(t, est["colofon"]), PageBreak()]


def _bloques(bloques, tipo, est, umbral):
    """Devuelve los flowables de una sección."""
    fs = []
    if tipo == "verso":
        for estrofa in bloques:
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
                    "umbral_estrofa_entera", "hyphenation", "subtitulo"}


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
