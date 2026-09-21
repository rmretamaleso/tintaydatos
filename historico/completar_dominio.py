#!/usr/bin/env python3
"""
completar_dominio.py — rellena catalogo_campos en los JSON de obras/ que no
lo tienen, tomando los datos de catalogo.csv.

Los primeros JSON del proyecto se escribieron antes de que existiera ese
bloque. Sin él, generar_epub no sabe qué color dar a la cubierta.

Empareja por catalogo_id y, si falta, por slug contra la URL del PDF.
No sobreescribe nada que ya esté escrito.

Uso:
    python3 completar_dominio.py              # informe
    python3 completar_dominio.py --escribir
"""
import csv
import glob
import json
import sys

CAMPOS = ["dominio", "titulo", "autor", "anio", "pais",
          "genero", "tema", "tipo", "puede_alojarse"]


def main():
    escribir = "--escribir" in sys.argv

    por_id, por_slug = {}, {}
    with open("catalogo.csv", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            por_id[str(fila.get("id", "")).strip()] = fila
            url = fila.get("url") or ""
            if "/ediciones/" in url:
                slug = url.rsplit("/", 1)[-1].replace("-tinta-y-datos.pdf", "")
                por_slug[slug] = fila

    rellenados, sin_pareja, ya_estaban = [], [], 0

    for ruta in sorted(glob.glob("obras/*.json")):
        with open(ruta, encoding="utf-8") as f:
            cfg = json.load(f)
        if (cfg.get("catalogo_campos") or {}).get("dominio"):
            ya_estaban += 1
            continue

        fila = por_id.get(str(cfg.get("catalogo_id", "")).strip())
        via = "catalogo_id"
        if not fila:
            fila = por_slug.get(cfg.get("slug", ""))
            via = "slug"
        if not fila:
            sin_pareja.append(ruta)
            continue

        nuevo = dict(cfg.get("catalogo_campos") or {})
        for c in CAMPOS:
            valor = (fila.get(c) or "").strip()
            if valor and not nuevo.get(c):
                nuevo[c] = valor
        cfg["catalogo_campos"] = nuevo
        rellenados.append((ruta, nuevo.get("dominio"), via))

        if escribir:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
                f.write("\n")

    print(f"JSON con dominio ya presente : {ya_estaban}")
    print(f"JSON completados             : {len(rellenados)}")
    print(f"Sin pareja en el catálogo    : {len(sin_pareja)}")
    for ruta, dom, via in rellenados:
        print(f"    {ruta.split('/')[-1]:34} -> {dom:12} (por {via})")
    for ruta in sin_pareja:
        print(f"    SIN PAREJA: {ruta}")
    if not escribir:
        print("\nSimulación. Añade --escribir para guardarlos.")


if __name__ == "__main__":
    main()
