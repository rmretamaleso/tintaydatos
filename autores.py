#!/usr/bin/env python3
"""
Registro de autores revisados y cuándo entran en dominio público.

Evita repetir la investigación: cada autor consultado queda anotado con su
estado, y el plazo se recalcula solo. Una pasada al año basta para saber qué
obra nueva se liberó.

    python3 autores.py                     # resumen
    python3 autores.py --libres            # disponibles hoy y aún sin publicar
    python3 autores.py --proximos 10       # qué se libera en los próximos 10 años
    python3 autores.py --ano 2028          # qué está libre a esa altura
    python3 autores.py --revisar           # fechas marcadas para comprobar

El plazo depende del país. La mayoría de Hispanoamérica aplica 70 años desde
la muerte del autor; España aplica 80 a quienes murieron antes de 1987, por
la disposición transitoria de su ley. La obra entra en dominio público el 1 de
enero del año siguiente al vencimiento.
"""
import argparse
import csv
import datetime
from pathlib import Path

PLAZO = 70
PLAZO_ESPANA_ANTIGUO = 80          # fallecidos antes de 1987


def libre_desde(fila):
    """Año a partir del cual la obra del autor es de dominio público."""
    muerte = fila.get("muerte", "").strip()
    if not muerte.isdigit():
        return None
    muerte = int(muerte)
    plazo = PLAZO_ESPANA_ANTIGUO if (fila["pais"].strip() == "España"
                                     and muerte < 1987) else PLAZO
    return muerte + plazo + 1


def cargar(ruta="autores.csv"):
    filas = list(csv.DictReader(open(ruta, encoding="utf-8")))
    for f in filas:
        f["libre_desde"] = libre_desde(f)
    return filas


def linea(f, ancho=30):
    fuente = "en la fuente" if f["en_fuente"].strip() == "si" else "—"
    aviso = " (*)" if f["fecha_fiable"].strip() != "si" else ""
    return (f"  {f['nombre'][:ancho]:<{ancho+1}} {f['pais'][:11]:<12} "
            f"{f['muerte']:>5}  libre {str(f['libre_desde'] or '?'):>5}   "
            f"{fuente}{aviso}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="autores.csv")
    ap.add_argument("--libres", action="store_true",
                    help="disponibles hoy y todavía sin edición propia")
    ap.add_argument("--proximos", type=int, metavar="N",
                    help="qué se libera en los próximos N años")
    ap.add_argument("--ano", type=int, help="qué está libre a esa altura")
    ap.add_argument("--revisar", action="store_true",
                    help="autores con fechas por comprobar")
    a = ap.parse_args()

    if not Path(a.csv).exists():
        raise SystemExit(f"No encuentro {a.csv}")
    filas = cargar(a.csv)
    hoy = datetime.date.today().year

    if a.revisar:
        pend = [f for f in filas if f["fecha_fiable"].strip() != "si"]
        print(f"{len(pend)} autor(es) con fechas por comprobar:\n")
        for f in sorted(pend, key=lambda x: x["nombre"]):
            print(linea(f))
        print("\nCorrige nacimiento/muerte en el CSV y pon fecha_fiable=si.")
        return

    if a.proximos is not None:
        corte = hoy + a.proximos
        prox = [f for f in filas if f["libre_desde"] and hoy < f["libre_desde"] <= corte]
        print(f"Se liberan entre {hoy + 1} y {corte}:\n")
        for f in sorted(prox, key=lambda x: (x["libre_desde"], x["nombre"])):
            print(linea(f))
        if not prox:
            print("  (ninguno)")
        return

    if a.ano is not None:
        nuevos = [f for f in filas if f["libre_desde"] and f["libre_desde"] <= a.ano
                  and f["libre_desde"] > hoy]
        print(f"Libres en {a.ano} que hoy no lo están:\n")
        for f in sorted(nuevos, key=lambda x: (x["libre_desde"], x["nombre"])):
            print(linea(f))
        if not nuevos:
            print("  (ninguno)")
        return

    if a.libres:
        libres = [f for f in filas
                  if f["libre_desde"] and f["libre_desde"] <= hoy
                  and f["estado"].strip() != "revisar_edicion"]
        en_fuente = [f for f in libres if f["en_fuente"].strip() == "si"]
        fuera = [f for f in libres if f["en_fuente"].strip() != "si"]
        print(f"DISPONIBLES Y EN textos.info ({len(en_fuente)}):\n")
        for f in sorted(en_fuente, key=lambda x: x["nombre"]):
            print(linea(f))
        print(f"\nDISPONIBLES PERO FUERA DE LA FUENTE ({len(fuera)}) "
              f"— harían falta otras fuentes:\n")
        for f in sorted(fuera, key=lambda x: x["nombre"]):
            print(linea(f))
        return

    # resumen
    protegidos = [f for f in filas if f["libre_desde"] and f["libre_desde"] > hoy]
    dudosos = [f for f in filas if f["estado"].strip() == "revisar_edicion"]
    en_fuente = [f for f in filas if f["en_fuente"].strip() == "si"]
    porcomprobar = [f for f in filas if f["fecha_fiable"].strip() != "si"]
    print(f"{len(filas)} autores revisados          (año actual: {hoy})")
    print(f"  {len(en_fuente):>3} están en textos.info")
    print(f"  {len(protegidos):>3} aún protegidos")
    print(f"  {len(dudosos):>3} libres pero con la edición en duda")
    print(f"  {len(porcomprobar):>3} con fechas por comprobar  (--revisar)")
    if protegidos:
        print("\nLos próximos en liberarse:\n")
        for f in sorted(protegidos, key=lambda x: x["libre_desde"])[:6]:
            print(linea(f))
    print("\n(*) fecha sin comprobar")


if __name__ == "__main__":
    main()
