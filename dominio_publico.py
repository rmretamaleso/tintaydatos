#!/usr/bin/env python3
"""
dominio_publico.py — convierte catalogo.csv en una matriz obra x país.

El dominio público es territorial: la misma obra puede estar libre en Chile y
protegida en México. Este script calcula el estado por país, marca lo que no se
puede decidir con los datos disponibles y genera las reglas de geobloqueo.

Uso:
    python3 dominio_publico.py catalogo.csv --init-autores   # crea autores_dominio.csv
    python3 dominio_publico.py catalogo.csv                  # calcula

ADVERTENCIA: los plazos de la tabla PAISES son un punto de partida documentado,
no asesoría legal. Antes de publicar, verifícalos con un abogado.
"""
import argparse
import csv
import os
import re
import sys
from datetime import date

ANIO_ACTUAL = date.today().year

# --------------------------------------------------------------------------
# Plazos post mortem auctoris por país.
#   plazo            : años tras la muerte del autor
#   regla_plazo_corto: aplica el art. 7.8 del Convenio de Berna a autores
#                      extranjeros (el plazo es el menor entre el local y el
#                      del país de origen)
#   transitoria_80   : España — 80 años p.m.a. para autores fallecidos antes
#                      del 7/12/1987 (disp. trans. 4ª LPI)
# --------------------------------------------------------------------------
PAISES = {
    # confianza: alta = norma verificada; media = recordada, contrastar;
    #            baja  = valor de partida, verificar SÍ o SÍ antes de publicar.
    "ES": {"nombre": "España",        "plazo": 70,  "corto": True,  "trans80": True,
           "confianza": "alta",  "fuente": "art. 26 LPI: 70 años, confirmado por la calculadora. La disp. trans. 4ª (80 años si falleció antes del 7/12/1987) NO la modela la calculadora, pero está documentada por CEDRO, la BNE y las guías universitarias"},
    "DE": {"nombre": "Alemania",      "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "MX": {"nombre": "México",        "plazo": 100, "corto": False, "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "CL": {"nombre": "Chile",         "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "AR": {"nombre": "Argentina",     "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "UY": {"nombre": "Uruguay",       "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "Ley 19.858 (dic. 2019) subió de 50 a 70 con retroactividad. La calculadora del Cerlalc devuelve 50: está desactualizada. Se mantiene 70 por ser lo conservador"},
    "US": {"nombre": "Estados Unidos","plazo": None,"corto": False, "trans80": False,
           "confianza": "alta",  "fuente": "publicación: libre si se publicó hasta hace 96 años"},
    "PR": {"nombre": "Puerto Rico",   "plazo": None,"corto": False, "trans80": False,
           "confianza": "alta",  "fuente": "rige la ley federal de EE. UU."},

    "CO": {"nombre": "Colombia",      "plazo": 80,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "PE": {"nombre": "Perú",          "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "EC": {"nombre": "Ecuador",       "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "VE": {"nombre": "Venezuela",     "plazo": 60,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "NI": {"nombre": "Nicaragua",     "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "PY": {"nombre": "Paraguay",      "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "CR": {"nombre": "Costa Rica",    "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "GB": {"nombre": "Reino Unido",   "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta", "fuente": "verificado con la calculadora del Cerlalc (2026)"},

    "CU": {"nombre": "Cuba",          "plazo": 50,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "BO": {"nombre": "Bolivia",       "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "SV": {"nombre": "El Salvador",   "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
    "FR": {"nombre": "Francia",       "plazo": 70,  "corto": True,  "trans80": False,
           "confianza": "alta",  "fuente": "verificado con la calculadora del Cerlalc (2026)"},
}

# Espacio Económico Europeo: entre miembros rige el trato nacional (art. 163.1
# LPI, doctrina Phil Collins), no la comparación de plazos del art. 7.8 de Berna.
EEE = {"ES", "DE", "FR"}

PAIS_A_ISO = {
    "España": "ES", "México": "MX", "Argentina": "AR", "Chile": "CL",
    "Colombia": "CO", "Perú": "PE", "Ecuador": "EC", "Venezuela": "VE",
    "Uruguay": "UY", "Cuba": "CU", "Alemania": "DE", "Estados Unidos": "US",
    "Nicaragua": "NI", "Puerto Rico": "US", "Bolivia": "BO", "Costa Rica": "CR",
    "Guatemala": "GT", "Paraguay": "PY", "Reino Unido": "GB", "Francia": "FR",
}

# Años de muerte precargados. Verificar uno por uno: son de memoria, no de fuente.
SEMILLA = {
    "Ramón María del Valle-Inclán": (1936, "ES"),
    "Federico García Lorca": (1936, "ES"),
    "Miguel de Unamuno": (1936, "ES"),
    "Carmen de Burgos": (1932, "ES"),
    "Emilia Pardo Bazán": (1921, "ES"),
    "Vicente Blasco Ibáñez": (1928, "ES"),
    "Santiago Ramón y Cajal": (1934, "ES"),
    "Horacio Quiroga": (1937, "UY"),
    "Javier de Viana": (1926, "UY"),
    "Delmira Agustini": (1914, "UY"),
    "José Pedro Bellán": (1930, "UY"),
    "Roberto Arlt": (1942, "AR"),
    "Leopoldo Lugones": (1938, "AR"),
    "Ricardo Güiraldes": (1927, "AR"),
    "Alfonsina Storni": (1938, "AR"),
    "José Seferino Álvarez «Fray Mocho»": (1903, "AR"),
    "Almafuerte": (1917, "AR"),
    "Vicente Huidobro": (1948, "CL"),
    "Teresa Wilms Montt": (1921, "CL"),
    "Ramón A. Laval": (1929, "CL"),
    "César Vallejo": (1938, "PE"),
    "Abraham Valdelomar": (1919, "PE"),
    "Pablo Palacio": (1947, "EC"),
    "Amado Nervo": (1919, "MX"),
    "Luis G. Urbina": (1934, "MX"),
    "José Eustasio Rivera": (1928, "CO"),
    "Teresa de la Parra": (1936, "VE"),
    "Gustavo Sánchez Galarraga": (1936, "CU"),
    "Charles Darwin": (1882, "GB"),
    "Miguel de Cervantes": (1616, "ES"),
}

# Por debajo de este año de publicación, el autor murió con certeza hace más de
# un siglo y ningún plazo p.m.a. sigue corriendo.
ANIO_SEGURO = 1850


def anio_de(valor):
    m = re.search(r"(1[3-9]\d\d|20\d\d)", str(valor))
    return int(m.group(1)) if m else None


def libre_hasta(anio_muerte, plazo):
    """El plazo corre desde el 1 de enero siguiente a la muerte."""
    return anio_muerte + plazo


def estado_us(anio_pub):
    if anio_pub is None:
        return "REVISAR", None
    if anio_pub <= ANIO_ACTUAL - 96:
        return "LIBRE", None
    return "REVISAR", None


def estado_en_pais(iso, anio_muerte, nac_autor, anio_pub):
    p = PAISES[iso]
    if p["plazo"] is None:          # EE. UU. y Puerto Rico: por año de publicación
        return estado_us(anio_pub)
    if anio_muerte is None:
        return "REVISAR", None

    plazo = p["plazo"]
    if p["trans80"] and anio_muerte < 1988:
        plazo = 80
    # Berna 7.8: para autor extranjero, el menor entre el plazo local y el de origen
    if p["corto"] and nac_autor and nac_autor != iso and not (iso in EEE and nac_autor in EEE):
        origen = PAISES.get(nac_autor)
        if origen and origen["plazo"]:
            plazo = min(plazo, origen["plazo"])

    hasta = libre_hasta(anio_muerte, plazo)
    return ("LIBRE" if ANIO_ACTUAL > hasta else "PROTEGIDO"), hasta


def cargar_autores(ruta):
    tabla = {}
    if not os.path.exists(ruta):
        return tabla
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            tabla[fila["autor"].strip()] = {
                "muerte": anio_de(fila.get("anio_muerte")),
                "nac": (fila.get("nacionalidad") or "").strip().upper() or None,
                "verificado": (fila.get("verificado") or "").strip().lower() in ("si", "true", "1"),
            }
    return tabla


def init_autores(filas, ruta):
    """Crea o AMPLÍA autores_dominio.csv. Nunca pisa un dato ya escrito: si el archivo
    existe, conserva cada fila tal cual y solo añade los autores nuevos del
    catálogo. Perder una tarde de verificación por volver a lanzar este comando
    no puede pasar."""
    campos = ["autor", "anio_muerte", "nacionalidad", "verificado", "fuente_fecha"]
    previos = {}
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                previos[fila["autor"].strip()] = fila

    autores = sorted({f["autor"].strip() for f in filas if f.get("autor")})
    nuevas, conservadas = 0, 0
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for a in autores:
            if a in previos:
                w.writerow({c: previos[a].get(c, "") for c in campos})
                conservadas += 1
            else:
                muerte, nac = SEMILLA.get(a, ("", ""))
                w.writerow({"autor": a, "anio_muerte": muerte, "nacionalidad": nac,
                            "verificado": "no" if muerte else "",
                            "fuente_fecha": "precargado, sin verificar" if muerte else ""})
                nuevas += 1

    huerfanos = [a for a in previos if a not in autores]
    verificados = sum(1 for a in previos.values()
                      if (a.get("verificado") or "").strip().lower() == "si")
    if conservadas:
        print(f"Actualizado {ruta}: {conservadas} filas conservadas intactas "
              f"({verificados} verificadas), {nuevas} autores nuevos añadidos.")
    else:
        pre = sum(1 for a in autores if a in SEMILLA)
        print(f"Escrito {ruta}: {len(autores)} autores, {pre} con año de muerte precargado "
              f"(marcados verificado=no), {len(autores)-pre} en blanco.")
    if huerfanos:
        print(f"  Aviso: {len(huerfanos)} autores de {ruta} ya no están en el catálogo "
              f"y se han eliminado: {', '.join(huerfanos[:5])}"
              + (" ..." if len(huerfanos) > 5 else ""))


def init_calibracion(out):
    """Escribe la hoja de consultas para la calculadora del Cerlalc,
    ordenada de menor a mayor confianza en el plazo que tengo cargado."""
    os.makedirs(out, exist_ok=True)
    ruta = os.path.join(out, "calculadora_calibracion.csv")
    rango = {"baja": 0, "media": 1, "alta": 2}
    isos = [i for i in PAISES if PAISES[i]["plazo"] is not None]
    isos.sort(key=lambda i: (rango[PAISES[i]["confianza"]], PAISES[i]["nombre"]))
    campos = ["orden", "prioridad", "iso", "pais_publicacion", "pais_origen", "tipo_obra",
              "postuma", "persona_juridica", "anio_muerte", "anio_publicacion", "mi_plazo",
              "anio_que_dice_la_calculadora", "plazo_deducido", "coincide"]
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for n, iso in enumerate(isos, 1):
            p = PAISES[iso]
            w.writerow({"orden": n, "prioridad": p["confianza"], "iso": iso,
                        "pais_publicacion": p["nombre"], "pais_origen": p["nombre"],
                        "tipo_obra": "Literaria y/o artística", "postuma": "no",
                        "persona_juridica": "no", "anio_muerte": 1950,
                        "anio_publicacion": 1945, "mi_plazo": p["plazo"],
                        "anio_que_dice_la_calculadora": "", "plazo_deducido": "", "coincide": ""})
    print(f"Escrito {ruta}: {len(isos)} consultas.")
    print("Abre https://cerlalc.org/calculadora-de-dominio-publico/ y rellena SOLO la")
    print("columna 'anio_que_dice_la_calculadora'. Después:")
    print(f"  python3 {os.path.basename(__file__)} <catalogo.csv> --calibrar {ruta}")


def calibrar(ruta):
    """Compara los plazos deducidos de la calculadora del Cerlalc con PAISES."""
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    sin_llenar, iguales, difieren = [], [], []
    for fila in filas:
        iso = (fila.get("iso") or "").strip().upper()
        if iso not in PAISES:
            continue
        # La calculadora muestra "Plazo de protección aplicado: N años". Si se
        # anota ahí, se usa tal cual; si no, se deduce del año que devuelve.
        directo = re.search(r"(\d{2,3})", str(fila.get("plazo_deducido") or ""))
        muerte = anio_de(fila.get("anio_muerte"))
        if directo:
            plazo_real = int(directo.group(1))
        else:
            anio_cal = anio_de(fila.get("anio_que_dice_la_calculadora"))
            if not anio_cal or not muerte:
                sin_llenar.append(iso)
                continue
            plazo_real = anio_cal - muerte - 1
        mio = PAISES[iso]["plazo"]
        (iguales if plazo_real == mio else difieren).append((iso, mio, plazo_real))

    print(f"Calibración contra la calculadora del Cerlalc ({ruta})")
    print(f"  coinciden : {len(iguales)}")
    print(f"  difieren  : {len(difieren)}")
    print(f"  sin llenar: {len(sin_llenar)} {' '.join(sin_llenar) if sin_llenar else ''}")
    if difieren:
        print()
        print("  CORREGIR en la tabla PAISES:")
        for iso, mio, real in difieren:
            print(f'    "{iso}" ({PAISES[iso]["nombre"]}): tengo {mio} años, la calculadora dice {real}')
    if not difieren and not sin_llenar:
        print("\n  Tabla validada por completo.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("catalogo")
    ap.add_argument("--autores", default="autores_dominio.csv")
    ap.add_argument("--out", default="salida")
    ap.add_argument("--establecimiento", default="DE",
                    help="país desde el que se produce y sube la edición (donde ocurre la "
                         "reproducción). Si una obra no es libre ahí, no basta geobloquear: "
                         "no se puede ni maquetar. Por defecto DE.")
    ap.add_argument("--init-autores", action="store_true")
    ap.add_argument("--init-calibracion", action="store_true",
                    help="genera la hoja de consultas para la calculadora del Cerlalc")
    ap.add_argument("--calibrar", metavar="CSV",
                    help="lee calculadora_calibracion.csv relleno y compara con la tabla PAISES")
    args = ap.parse_args()

    with open(args.catalogo, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    if args.init_autores:
        init_autores(filas, args.autores)
        return

    if args.init_calibracion:
        init_calibracion(args.out)
        return

    if args.calibrar:
        if not os.path.exists(args.calibrar):
            sys.exit(f"No existe {args.calibrar}.\n"
                     f"Genérala primero con:\n"
                     f"  python3 {os.path.basename(__file__)} {args.catalogo} --init-calibracion")
        calibrar(args.calibrar)
        return

    autores = cargar_autores(args.autores)
    if not autores:
        sys.exit(f"No existe {args.autores}. Ejecuta primero --init-autores.")

    os.makedirs(args.out, exist_ok=True)
    isos = list(PAISES.keys())
    matriz, revisar = [], []

    for fila in filas:
        autor = (fila.get("autor") or "").strip()
        anio_pub = anio_de(fila.get("anio"))
        info = autores.get(autor, {})
        muerte, nac = info.get("muerte"), info.get("nac")
        tipo = (fila.get("tipo") or "").strip()
        motivos = []

        # 1. Licencia en vez de dominio público: obligaciones propias, no p.m.a.
        if tipo and not tipo.lower().startswith("dominio público"):
            motivos.append(f"no es dominio público sino '{tipo}': revisar licencia y atribución")

        # 2. Obra antigua: segura sin necesidad de fecha de muerte
        segura_por_antiguedad = anio_pub is not None and anio_pub <= ANIO_SEGURO

        if muerte is None and not segura_por_antiguedad:
            motivos.append("falta año de muerte del autor")
        if muerte is not None and not info.get("verificado"):
            motivos.append("año de muerte sin verificar")

        # 3. Edición muy posterior a la muerte: traductor, prologuista o editor
        #    con derechos propios sobre esa edición concreta
        if muerte and anio_pub and anio_pub > muerte + 20:
            motivos.append(f"edición de {anio_pub} es {anio_pub-muerte} años posterior a la muerte "
                           f"del autor: posible traducción/prólogo/edición crítica con derechos propios")

        estados = {}
        for iso in isos:
            if segura_por_antiguedad and PAISES[iso]["plazo"] is not None:
                estados[iso] = ("LIBRE", None)
            else:
                estados[iso] = estado_en_pais(iso, muerte, nac, anio_pub)

        # El país de establecimiento es el suelo: allí ocurre la reproducción
        # (maquetar el PDF y subirlo), y eso no lo arregla ningún geobloqueo.
        est = args.establecimiento.upper()
        est_estado = estados.get(est, ("REVISAR", None))[0]
        bloquear = [i for i in isos if estados[i][0] == "PROTEGIDO" and i != est]
        # Solo bloquea la decisión la falta de datos del autor o la duda en el
        # país de establecimiento. Que EE. UU. quede sin decidir no invalida el
        # resto: se anota aparte y se geobloquea por precaución.
        faltan_datos = muerte is None and not segura_por_antiguedad
        sin_decidir = [i for i in isos if estados[i][0] == "REVISAR"]
        if est_estado == "PROTEGIDO":
            accion = "NO_PUBLICAR"
        elif faltan_datos or est_estado == "REVISAR":
            accion = "REVISAR"
        elif sin_decidir:
            bloquear = sorted(set(bloquear) | set(sin_decidir))
            accion = "GEOBLOQUEAR:" + ",".join(bloquear)
        elif bloquear:
            accion = "GEOBLOQUEAR:" + ",".join(bloquear)
        else:
            accion = "PUBLICAR"

        reg = {"id": fila.get("id"), "titulo": fila.get("titulo"), "autor": autor,
               "anio": fila.get("anio"), "anio_muerte": muerte or "", "tipo": tipo,
               "accion": accion}
        for iso in isos:
            est, hasta = estados[iso]
            reg[iso] = est
            reg[f"{iso}_libre_en"] = hasta + 1 if (hasta and est == "PROTEGIDO") else ""
        matriz.append(reg)

        if est_estado == "PROTEGIDO":
            motivos.insert(0, f"PROTEGIDA EN {PAISES[est]['nombre']}, país desde el que publicas: "
                              f"no se puede maquetar ni subir, el geobloqueo no lo resuelve")
        if motivos or any(estados[i][0] == "PROTEGIDO" for i in isos):
            prot = [f"{i}(hasta {estados[i][1]})" for i in isos if estados[i][0] == "PROTEGIDO"]
            revisar.append({"id": fila.get("id"), "titulo": fila.get("titulo"), "autor": autor,
                            "anio": fila.get("anio"),
                            "protegida_en": "; ".join(prot),
                            "motivos": " | ".join(motivos)})

    campos = ["id", "titulo", "autor", "anio", "anio_muerte", "tipo", "accion"]
    for iso in isos:
        campos += [iso, f"{iso}_libre_en"]
    with open(os.path.join(args.out, "matriz_paises.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(matriz)

    with open(os.path.join(args.out, "revisar.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "titulo", "autor", "anio", "protegida_en", "motivos"])
        w.writeheader()
        w.writerows(revisar)

    # Reglas de geobloqueo: por cada país, las obras que hay que ocultar
    lineas = ["# Geobloqueo por país", "",
              "Basado en la sentencia TJUE C-788/24 (9/7/2026): publicar una obra de",
              "dominio público es lícito aunque siga protegida en otro país, si un",
              "bloqueo geográfico actualizado impide el acceso desde allí.", ""]
    for iso in isos:
        ids = [m["id"] for m in matriz if m[iso] == "PROTEGIDO"]
        rev = [m["id"] for m in matriz if m[iso] == "REVISAR"]
        if ids or rev:
            lineas.append(f"## {PAISES[iso]['nombre']} ({iso})")
            lineas.append(f"- Bloquear: {len(ids)} obras -> ids {', '.join(map(str, ids[:40]))}"
                          + (" ..." if len(ids) > 40 else ""))
            lineas.append(f"- Sin decidir: {len(rev)} obras")
            lineas.append("")
    lineas += ["## Expresión para Cloudflare (WAF, acción Block)", "",
               "```", '(ip.geoip.country eq "MX" and http.request.uri.path contains "/ediciones/<slug>")', "```",
               "", "Genera una regla por país usando los ids de arriba, o marca cada",
               "edición con una cabecera de país en el worker y bloquea por ella."]
    with open(os.path.join(args.out, "geobloqueo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")

    total = len(matriz)
    print(f"Obras analizadas: {total}")
    print("(confianza del plazo entre paréntesis)")
    for iso in isos:
        prot = sum(1 for m in matriz if m[iso] == "PROTEGIDO")
        rev = sum(1 for m in matriz if m[iso] == "REVISAR")
        libre = total - prot - rev
        print(f"  {PAISES[iso]['nombre']:16} [{PAISES[iso]['confianza']:5}] libre {libre:4}   protegida {prot:4}   sin decidir {rev:4}")
    import collections
    acc = collections.Counter(m["accion"].split(":")[0] for m in matriz)
    print()
    print(f"Acción (publicando desde {PAISES[args.establecimiento.upper()]['nombre']}):")
    for k in ("PUBLICAR", "GEOBLOQUEAR", "NO_PUBLICAR", "REVISAR"):
        print(f"  {k:12} {acc.get(k, 0):4}")
    print(f"\nFilas en revisar.csv: {len(revisar)}")
    print(f"Salida en {args.out}/")


if __name__ == "__main__":
    main()
