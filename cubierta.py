#!/usr/bin/env python3
"""
cubierta.py — cubierta tipográfica para los EPUB, en el estilo de la portada
de los PDF: título, autor con sus fechas, año y el sello de colección.

El color lo marca el dominio del catálogo, tomado de la paleta que ya usa
tintaydatos.com. Misma composición para todo el catálogo: lo que cambia es
el tono, no la estructura, de modo que se lea como una colección.

    import cubierta
    cubierta.generar(obra, "cubierta.png", dominio="Literatura")
"""
from PIL import Image, ImageDraw, ImageFont

# Paleta tomada de index.html
CREMA = "#fbf6e8"
TINTA = "#2b2b2b"
COLORES = {
    "Literatura": "#6B4C8C",              # violeta
    "Ciencia": "#3d6656",                 # verde bosque
    "Revistas y repositorios": "#2a6f8e",  # azul petróleo
    "Libros de Colegio": "#8a5a3c",       # terracota
}
COLOR_POR_DEFECTO = "#6B4C8C"

# Liberation Serif es métricamente compatible con Times, la de los PDF
BASE = "/usr/share/fonts/truetype/liberation"
FUENTES = {
    "titulo": f"{BASE}/LiberationSerif-Bold.ttf",
    "autor": f"{BASE}/LiberationSerif-Italic.ttf",
    "dato": f"{BASE}/LiberationSerif-Regular.ttf",
    "sello": f"{BASE}/LiberationMono-Regular.ttf",
}

ANCHO, ALTO = 1200, 1800   # proporción 2:3, la habitual en bibliotecas
MARGEN = 130


def _fuente(clave, tam):
    try:
        return ImageFont.truetype(FUENTES[clave], tam)
    except OSError:
        return ImageFont.load_default()


def _ajustar(dib, texto, fuente, ancho_max):
    """Parte el texto en líneas que quepan en ancho_max."""
    palabras, lineas, actual = str(texto).split(), [], ""
    for p in palabras:
        prueba = f"{actual} {p}".strip()
        if dib.textlength(prueba, font=fuente) <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def _centrado(dib, texto, fuente, y, color):
    w = dib.textlength(texto, font=fuente)
    dib.text(((ANCHO - w) / 2, y), texto, font=fuente, fill=color)
    return y + fuente.size * 1.35


def generar(obra, salida, dominio=None):
    color = COLORES.get(dominio, COLOR_POR_DEFECTO)
    img = Image.new("RGB", (ANCHO, ALTO), CREMA)
    d = ImageDraw.Draw(img)

    # Banda superior: identifica el dominio de un vistazo en una estantería
    d.rectangle([0, 0, ANCHO, 26], fill=color)

    util = ANCHO - 2 * MARGEN
    y = 430

    # Título: el tamaño baja si el título es largo, para no partirlo en cuatro
    titulo = str(obra.get("titulo", ""))
    for tam in (96, 84, 72, 62, 54):
        f_tit = _fuente("titulo", tam)
        lineas = _ajustar(d, titulo, f_tit, util)
        if len(lineas) <= 3:
            break
    for linea in lineas:
        y = _centrado(d, linea, f_tit, y, TINTA)

    # Filete de color bajo el título
    # Filete grueso: a tamaño de miniatura uno fino desaparece
    y += 46
    d.line([(ANCHO / 2 - 190, y), (ANCHO / 2 + 190, y)], fill=color, width=7)
    y += 78

    f_aut = _fuente("autor", 52)
    for linea in _ajustar(d, obra.get("autor", ""), f_aut, util):
        y = _centrado(d, linea, f_aut, y, TINTA)

    fechas = obra.get("fechas_autor")
    if fechas:
        y = _centrado(d, str(fechas), _fuente("dato", 34), y + 8, "#6b6b6b")

    if obra.get("anio"):
        y = _centrado(d, str(obra["anio"]), _fuente("dato", 36), y + 26, "#6b6b6b")

    # Sello de colección al pie, en el color del dominio
    f_sello = _fuente("sello", 28)
    sello = "TINTA Y DATOS"
    w = d.textlength(sello, font=f_sello)
    d.text(((ANCHO - w) / 2, ALTO - 210), sello, font=f_sello, fill=color)

    f_sub = _fuente("sello", 22)
    sub = "CATÁLOGO SEMILLA"
    w = d.textlength(sub, font=f_sub)
    d.text(((ANCHO - w) / 2, ALTO - 165), sub, font=f_sub, fill="#8a8a8a")

    # salida admite una ruta o un buffer, para empaquetar sin tocar disco
    img.save(salida, "PNG", optimize=True)
    return salida
