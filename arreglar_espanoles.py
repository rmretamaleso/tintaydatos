#!/usr/bin/env python3
"""Corrige la estructura de las obras que avisaron.

Dos patrones: novelas cuyos capítulos van en h3 bajo partes en h2, y obras que
abren con dedicatoria o epígrafe antes del primer capítulo.
"""
import json, pathlib

ORDEN = ["slug","titulo","autor","anio","tipo","autor_slug","piezas_fuente","orden",
         "url","catalogo","fuente","catalogo_id","catalogo_campos","nivel_parte",
         "nivel_capitulo","nivel_seccion","patron_seccion","preliminares",
         "piezas_independientes","esperados","opciones"]

# capítulos en h3 bajo partes en h2
PARTES = ["va-morsamor","va-comendadormendoza","va-cartasamericanas",
 "va-nuevascartasameric","va-superhombreotrasno","va-varioscolores","va-vuelapluma",
 "va-cuentoschascarrill","va-cuentosdialogos","va-algotodo","va-leyendasantiguoori",
 "va-estragosamorcelos",
 "vi-vivamidueno","vi-cortemilagros","vi-bazaespadas","vi-caradios",
 "vi-comediasbarbaras","vi-aguilablason","vi-caraplata","vi-divinaspalabras",
 "vi-martescarnaval","vi-romancelobos","vi-tabladomarionetasp","vi-retabloavaricialuj",
 "vi-floralmendro","vi-corteamor","vi-femeninas","vi-finrevolucionario",
 "vi-florsantidad","vi-jardinumbrio","vi-lamparamaravillosa","vi-pipakif",
 "al-cuentosamatorios","al-novelascortas","al-alpujarra","al-viajesporespana",
 "al-escandalo","al-finalnorma","al-ninobola","al-prodiga","al-capitanveneno",
 "al-historietasnaciona","al-narracionesinveros","al-clavo","al-seisvelos"]

# obras con tres niveles
TRES = {"vi-tiranobanderas": "h4", "al-cuentosamatorios": "h4"}

# dedicatoria o epígrafe antes del primer capítulo
PRELIM = {"va-morsamor":"Portada","va-asclepigenia":"Epígrafe",
 "va-cuentosdialogos":"Dedicatoria","va-estragosamorcelos":"Epígrafe",
 "va-geniofigura":"Dedicatoria","va-leyendasantiguoori":"Prólogo",
 "va-mariquitaantonio":"Dedicatoria","vi-corteamor":"Dedicatoria",
 "vi-epitalamio":"Dedicatoria","vi-jardinumbrio":"Dedicatoria",
 "vi-lamparamaravillosa":"Dedicatoria","al-capitanveneno":"Dedicatoria",
 "al-escandalo":"Dedicatoria","al-narracionesinveros":"Dedicatoria"}

n = 0
for archivo in set(PARTES) | set(PRELIM):
    p = pathlib.Path(f"obras/{archivo}.json")
    if not p.exists():
        print(f"  (no existe {archivo})"); continue
    c = json.loads(p.read_text(encoding="utf-8"))
    if archivo in PARTES:
        c["nivel_parte"] = "h2"
        c["nivel_capitulo"] = "h3"
        if archivo in TRES:
            c["nivel_seccion"] = TRES[archivo]
            c["patron_seccion"] = "^(.+)$"
    if archivo in PRELIM:
        c["preliminares"] = PRELIM[archivo]
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n += 1
print(f"{n} configuraciones corregidas")
