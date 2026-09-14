#!/usr/bin/env python3
"""
fusionar_autores.py — lleva los años de muerte verificados de
legal/autores_dominio.csv al registro principal autores.csv.

No inventa ni sobrescribe a ciegas: solo toca las filas cuyo año fue
verificado a mano, informa de cada discrepancia y deja intacto todo lo demás
(alias, slug, país, nacimiento, notas).

Uso:
    python3 fusionar_autores.py                 # informe, sin escribir
    python3 fusionar_autores.py --escribir      # aplica los cambios
"""
import csv
import shutil
import sys

PRINCIPAL = "autores.csv"
DOMINIO = "legal/autores_dominio.csv"


def main():
    escribir = "--escribir" in sys.argv

    with open(PRINCIPAL, encoding="utf-8") as f:
        lector = csv.DictReader(f)
        campos = list(lector.fieldnames)
        filas = list(lector)

    verificados = {}
    with open(DOMINIO, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r.get("verificado") or "").strip().lower() == "si" and r.get("anio_muerte"):
                verificados[r["autor"].strip()] = r["anio_muerte"].strip()

    rellenados, confirmados, discrepantes, ausentes = [], [], [], []
    presentes = {(r.get("nombre") or "").strip() for r in filas}

    for fila in filas:
        nombre = (fila.get("nombre") or "").strip()
        nuevo = verificados.get(nombre)
        if not nuevo:
            continue
        actual = (fila.get("muerte") or "").strip()
        if not actual:
            fila["muerte"] = nuevo
            fila["fecha_fiable"] = "verificado"
            rellenados.append((nombre, nuevo))
        elif actual == nuevo:
            if (fila.get("fecha_fiable") or "").strip() != "verificado":
                fila["fecha_fiable"] = "verificado"
            confirmados.append(nombre)
        else:
            discrepantes.append((nombre, actual, nuevo))

    for nombre in verificados:
        if nombre not in presentes:
            ausentes.append(nombre)

    print(f"Autores verificados en {DOMINIO}: {len(verificados)}")
    print(f"  ya coincidían                 : {len(confirmados)}")
    print(f"  huecos rellenados             : {len(rellenados)}")
    print(f"  DISCREPANCIAS                 : {len(discrepantes)}")
    print(f"  no existen en {PRINCIPAL}     : {len(ausentes)}")

    if discrepantes:
        print("\n  Revisa estas a mano. NO se han tocado:")
        for nombre, actual, nuevo in discrepantes:
            print(f"    {nombre}: {PRINCIPAL} dice {actual}, verificado dice {nuevo}")
    if ausentes:
        print(f"\n  Sin ficha en {PRINCIPAL} (el nombre puede estar escrito distinto):")
        for n in ausentes[:15]:
            print(f"    {n}")
        if len(ausentes) > 15:
            print(f"    ... y {len(ausentes)-15} más")

    if not escribir:
        print("\nSimulación. Vuelve a lanzarlo con --escribir para aplicar.")
        return

    shutil.copy(PRINCIPAL, PRINCIPAL + ".bak")
    with open(PRINCIPAL, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"\nEscrito {PRINCIPAL} (copia de seguridad en {PRINCIPAL}.bak)")


if __name__ == "__main__":
    main()
