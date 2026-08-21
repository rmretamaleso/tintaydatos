#!/usr/bin/env python3
"""
Revisa rimas_completo.txt y, opcionalmente, aplica correcciones documentadas.

  python3 revisar_rimas.py                          # solo diagnóstico
  python3 revisar_rimas.py --aplicar correcciones.tsv --salida rimas_corregido.txt

correcciones.tsv: 4 columnas separadas por TAB
  RIMA <TAB> verso tal como está <TAB> verso corregido <TAB> fuente/justificación
Las correcciones que no calcen exactamente se avisan y NO se aplican en silencio.
"""
import argparse, re, sys
from collections import Counter

ROMANO = re.compile(r"^[IVXLC]+$")

# Puntos sospechosos conocidos: (etiqueta, regex)
VIGILANCIA = [
    ("resto de navegación web", r"Arriba\s*Abajo"),
    ("¿'don ángeles' por 'dos ángeles'?", r"\bdon\s+[áa]ngeles\b"),
    ("verso truncado LXXVI", r"pintados\s*$"),
    ("¿'eras' por 'creas'?", r"pues no lo eras"),
    ("¿'deserto' por 'desierto'?", r"\bdeserto\b"),
    ("¿'intérvalos' por 'intervalos'?", r"intérvalos"),
    ("¿'oiga' por 'oigo'?", r"\by oiga al tiempo\b"),
    ("comilla sin pareja", r"^[^«]*»[^«]*$"),
    ("línea que acaba en preposición/artículo",
     r"\b(?:a|de|en|con|por|para|el|la|los|las|un|una|unos|unas|y|o|que|su|sus|mi|tu)\s*$"),
]


def cargar(ruta):
    txt = open(ruta, encoding="utf-8").read()
    partes = txt.split("\n", 2)
    cabecera, cuerpo = "\n".join(partes[:2]), partes[2]
    rimas, num, buf = [], None, []
    for bloque in re.split(r"\n\s*\n", cuerpo.strip()):
        lineas = [l.rstrip() for l in bloque.split("\n") if l.strip()]
        if not lineas:
            continue
        if ROMANO.match(lineas[0].strip()):
            if num:
                rimas.append((num, buf))
            num, buf = lineas[0].strip(), []
            lineas = lineas[1:]
        if num and lineas:
            buf.append(lineas)
    if num:
        rimas.append((num, buf))
    return cabecera, rimas


def escribir(cabecera, rimas, salida):
    with open(salida, "w", encoding="utf-8") as f:
        f.write(cabecera + "\n\n")
        for num, estrofas in rimas:
            f.write(num + "\n")
            f.write("\n\n".join("\n".join(e) for e in estrofas))
            f.write("\n\n")
    print(f"Escrito: {salida}")


def diagnostico(rimas, contexto=False):
    print("=== 1. Estrofas de largo anómalo (posible salto de estrofa perdido) ===")
    hallazgos = 0
    for num, estrofas in rimas:
        if len(estrofas) < 3:
            continue
        # las acotaciones de voz (>>) no cuentan para el largo típico
        idx = [i for i, e in enumerate(estrofas)
               if not (len(e) == 1 and e[0].startswith(">>"))]
        largos_ref = [len(estrofas[i]) for i in idx]
        if len(largos_ref) < 3:
            continue
        modo = Counter(largos_ref).most_common(1)[0][0]
        largos = [len(e) for e in estrofas]
        for i, n in enumerate(largos, 1):
            if i - 1 not in idx:
                continue
            if n > modo and n % modo == 0 and n != modo:
                print(f"  {num:<8} estrofa {i}: {n} versos (el resto usa {modo}) "
                      f"-> ¿son {n // modo} estrofas pegadas?")
                print(f"           primer verso: «{estrofas[i-1][0]}»")
                hallazgos += 1
    if not hallazgos:
        print("  (sin anomalías)")

    print("\n=== 2. Puntos vigilados ===")
    hallazgos = 0
    for etiqueta, patron in VIGILANCIA:
        rx = re.compile(patron, re.I | re.M)
        for num, estrofas in rimas:
            for e in estrofas:
                for v in e:
                    if v.startswith(">>"):
                        continue
                    if rx.search(v):
                        print(f"  [{etiqueta}] {num}: «{v}»")
                        if contexto:
                            for w in e:
                                print(f"        {'>' if w is v else ' '} {w}")
                            print()
                        hallazgos += 1
    if not hallazgos:
        print("  (sin hallazgos)")

    n = sum(sum(len(e) for e in es) for _, es in rimas)
    print(f"\n=== Totales: {len(rimas)} rimas | "
          f"{sum(len(es) for _, es in rimas)} estrofas | {n} versos ===")


def cortar(rimas, ruta_tsv):
    """Divide estrofas: cada regla marca el verso que debe INICIAR una estrofa nueva."""
    reglas = []
    for i, ln in enumerate(open(ruta_tsv, encoding="utf-8"), 1):
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        campos = ln.rstrip("\n").split("\t")
        if len(campos) < 2:
            sys.exit(f"{ruta_tsv}:{i}: hacen falta al menos 2 columnas separadas por TAB")
        reglas.append([c.strip() for c in (campos + [""] * 3)[:3]])

    hechas, fallidas = 0, []
    for rima_obj, inicio, nota in reglas:
        hecho = False
        for k, (num, estrofas) in enumerate(rimas):
            if num != rima_obj:
                continue
            nuevas = []
            for e in estrofas:
                pos = next((j for j, v in enumerate(e) if j > 0 and v.strip() == inicio), None)
                if pos is None:
                    nuevas.append(e)
                else:
                    nuevas.extend([e[:pos], e[pos:]])
                    hecho = True
            rimas[k] = (num, nuevas)
        if hecho:
            hechas += 1
            print(f"  CORTE {rima_obj}: nueva estrofa desde «{inicio}»   [{nota}]")
        else:
            fallidas.append((rima_obj, inicio))

    for rima_obj, inicio in fallidas:
        print(f"  FALLA {rima_obj}: «{inicio}» no existe, o ya inicia estrofa", file=sys.stderr)
    print(f"\n{hechas} cortes aplicados, {len(fallidas)} fallidos.")
    if fallidas:
        sys.exit("Corrige el .tsv y reintenta. No escribo nada si algo no calzó.")
    return rimas


def aplicar(rimas, ruta_tsv):
    reglas = []
    for i, ln in enumerate(open(ruta_tsv, encoding="utf-8"), 1):
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        campos = ln.rstrip("\n").split("\t")
        if len(campos) < 3:
            sys.exit(f"{ruta_tsv}:{i}: hacen falta al menos 3 columnas separadas por TAB")
        reglas.append([c.strip() for c in (campos + [""] * 4)[:4]])

    aplicadas, fallidas = 0, []
    for rima_obj, orig, nuevo, nota in reglas:
        hecho = False
        for num, estrofas in rimas:
            if num != rima_obj:
                continue
            for e in estrofas:
                for j, v in enumerate(e):
                    if v.strip() == orig:
                        e[j] = nuevo
                        hecho = True
        if hecho:
            aplicadas += 1
            print(f"  OK   {rima_obj}: «{orig}» -> «{nuevo}»   [{nota}]")
        else:
            fallidas.append((rima_obj, orig))

    for rima_obj, orig in fallidas:
        print(f"  FALLA {rima_obj}: no encontré exactamente «{orig}»", file=sys.stderr)
    print(f"\n{aplicadas} aplicadas, {len(fallidas)} fallidas.")
    if fallidas:
        sys.exit("Corrige el .tsv y reintenta. No escribo nada si algo no calzó.")
    return rimas


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="rimas_completo.txt")
    ap.add_argument("--aplicar")
    ap.add_argument("--cortes")
    ap.add_argument("--contexto", action="store_true")
    ap.add_argument("--salida", default="rimas_corregido.txt")
    a = ap.parse_args()

    cabecera, rimas = cargar(a.entrada)
    if a.aplicar or a.cortes:
        if a.cortes:
            rimas = cortar(rimas, a.cortes)
        if a.aplicar:
            rimas = aplicar(rimas, a.aplicar)
        escribir(cabecera, rimas, a.salida)
    else:
        diagnostico(rimas, a.contexto)
