#!/usr/bin/env python3
"""
generar_manifiesto.py — construye el manifiesto de geobloqueo para el Worker.

Lee la matriz por país y produce un JSON { "slug-del-pdf": ["MX","US"], ... }
con solo las obras que tienen alguna restricción. Las libres no se listan:
lo que no está en el manifiesto se sirve sin condiciones.

Uso:
    python3 generar_manifiesto.py catalogo_actualizado.csv salida/matriz_paises.csv
"""
import csv
import json
import sys
from datetime import date
from urllib.parse import urlparse

DOMINIO = "archivos.tintaydatos.com"


def slugs_de(fila):
    """Devuelve todos los slugs de una ficha: el principal y las piezas múltiples."""
    urls = [fila.get("url") or ""]
    extra = (fila.get("urls") or "").strip()
    if extra:
        for trozo in extra.split("|"):
            urls.append(trozo.split("::")[-1])
    salida = []
    for u in urls:
        if DOMINIO in u:
            ruta = urlparse(u).path.lstrip("/")
            if ruta:
                salida.append(ruta)
    return salida


def main():
    if len(sys.argv) < 3:
        sys.exit("uso: generar_manifiesto.py catalogo.csv matriz_paises.csv")
    cat = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    mat = {r["id"]: r for r in csv.DictReader(open(sys.argv[2], encoding="utf-8"))}

    manifiesto, sin_decidir, libres = {}, [], 0
    for fila in cat:
        rutas = slugs_de(fila)
        if not rutas:
            continue
        accion = mat.get(fila["id"], {}).get("accion", "")
        titulo = (fila.get("titulo") or "").strip()
        autor = (fila.get("autor") or "").strip()
        if accion.startswith("GEOBLOQUEAR"):
            paises = accion.split(":")[1].split(",")
            for r in rutas:
                manifiesto[r] = {"p": paises, "t": titulo, "a": autor}
        elif accion == "REVISAR":
            sin_decidir.append(fila["id"])
            # criterio conservador: sin datos, se bloquea donde el plazo es más largo
            for r in rutas:
                manifiesto[r] = {"p": ["MX", "CO", "US", "PR"], "t": titulo, "a": autor}
        else:
            libres += 1

    salida = {
        "generado": date.today().isoformat(),
        "bloqueos": manifiesto,
    }
    with open("manifiesto_bloqueo.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=0, sort_keys=True)

    tam = len(json.dumps(salida))
    print(f"manifiesto_bloqueo.json: {len(manifiesto)} rutas con restricción, "
          f"{libres} sin restricción ({tam/1024:.1f} KB)")
    if sin_decidir:
        print(f"  {len(sin_decidir)} fichas sin datos suficientes: bloqueadas por precaución "
              f"en MX, CO, US y PR")
    por = {}
    for entrada in manifiesto.values():
        for p in entrada["p"]:
            por[p] = por.get(p, 0) + 1
    print("  bloqueos por país:", dict(sorted(por.items(), key=lambda x: -x[1])))


if __name__ == "__main__":
    main()
