#!/usr/bin/env python3
"""Declara el cuarto nivel en las obras que aún descartaban encabezados."""
import json, pathlib

ORDEN = ["slug","titulo","autor","anio","tipo","url","catalogo","fuente","catalogo_id",
         "catalogo_campos","nivel_parte","nivel_capitulo","nivel_seccion",
         "patron_seccion","preliminares","piezas_independientes","esperados","opciones"]

CAMBIOS = {
 # cuarto nivel con numerales o escenas
 "va-varioscolores":      {"nivel_seccion":"h4","patron_seccion":"^(.+)$"},
 "vi-bazaespadas":        {"nivel_seccion":"h4"},
 "vi-comediasbarbaras":   {"nivel_seccion":"h4","patron_seccion":"^(.+)$"},
 "vi-cortemilagros":      {"nivel_seccion":"h4"},
 "vi-finrevolucionario":  {"nivel_seccion":"h4"},
 "al-historietasnaciona": {"nivel_seccion":"h4"},
 # Tirano Banderas: libros en h3, numerales en h4
 "vi-tiranobanderas":     {"nivel_parte":"h2","nivel_capitulo":"h3",
                           "nivel_seccion":"h4"},
 # La Pipa de Kif es poesía, no prosa
 "vi-pipakif":            {"tipo":"verso"},
}

n = 0
for archivo, extra in CAMBIOS.items():
    p = pathlib.Path(f"obras/{archivo}.json")
    if not p.exists():
        print(f"  (no existe {archivo})"); continue
    c = json.loads(p.read_text(encoding="utf-8"))
    c.update(extra)
    if extra.get("tipo") == "verso":
        c.get("opciones", {}).pop("hyphenation", None)   # el verso no se parte
        c.setdefault("catalogo_campos", {})["genero"] = "Poesía"
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  {c['titulo'][:34]:<36} {', '.join(f'{k}={v}' for k,v in extra.items())}")
    n += 1
print(f"\n{n} configuraciones corregidas")
