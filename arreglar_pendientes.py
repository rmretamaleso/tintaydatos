#!/usr/bin/env python3
"""Declara la estructura de las obras que avisaban.

Todas siguen el mismo patrón: partes en h2, capítulos en h3 y numerales en h4.
Es la estructura habitual de la novela decimonónica, ya vista en Valera y
Alarcón.
"""
import json, pathlib

ORDEN = ["slug","titulo","autor","anio","tipo","autor_slug","piezas_fuente","orden",
         "url","catalogo","fuente","catalogo_id","catalogo_campos","nivel_parte",
         "nivel_capitulo","nivel_seccion","patron_seccion","preliminares",
         "piezas_independientes","esperados","opciones"]

OBRAS = """pg-abuelo pg-aitatettauen pg-angelguerra pg-audaz pg-cienmilhijossanl
pg-desheredada pg-doctorcenteno pg-electra pg-episodiosnaciona pg-familialeonroch
pg-fontanaoro pg-gerona pg-gloria pg-halma pg-locacasa pg-loprohibido pg-nazarin
pg-plumaviento pg-razonsinrazon pg-realidad pg-sanquintin pg-sombra
pg-torquemadacruz pg-torquemadapurgat pg-torquemadasanped be-caudillomanosroj
be-creeddios be-esraro be-maeseperezorgani be-monteanimas be-rosapasion
rc-caballerobotasaz rc-mimadre mz-desenganosamoros mz-novelasamorosase""".split()

n = 0
for archivo in OBRAS:
    p = pathlib.Path(f"obras/{archivo}.json")
    if not p.exists():
        print(f"  (no existe {archivo})"); continue
    c = json.loads(p.read_text(encoding="utf-8"))
    c["nivel_parte"] = "h2"
    c["nivel_capitulo"] = "h3"
    c["nivel_seccion"] = "h4"
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n += 1
print(f"{n} configuraciones: partes h2, capítulos h3, numerales h4")
