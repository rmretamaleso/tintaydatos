#!/usr/bin/env python3
"""Completa la tanda latinoamericana.

1. Crea las obras de autores cuya única pieza quedó fuera por no tener
   encabezados: son novelas o poemarios breves, y sin esto se pierden cuatro
   países que el catálogo no tiene.
2. Declara los preliminares en las obras que avisaban.
"""
import json, pathlib

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
ORDEN = ["slug","titulo","autor","anio","tipo","autor_slug","piezas_fuente","orden",
         "url","catalogo","fuente","catalogo_id","catalogo_campos","nivel_parte",
         "nivel_capitulo","nivel_seccion","patron_seccion","preliminares",
         "piezas_independientes","esperados","opciones"]

SUELTAS = [
 # archivo, autor_slug, nombre, país, género, id
 ("cr-*", "carlos-reyles", "Carlos Reyles", "Uruguay", "Novela", 769),
 ("at-*", "jose-alonso-y-trelles", "José Alonso y Trelles", "Uruguay", "Poesía", 770),
 ("bc-*", "luis-benjamin-cisneros", "Luis Benjamín Cisneros", "Perú", "Novela", 771),
 ("gz-*", "manuel-gonzalez-zeledon", "Manuel González Zeledón", "Costa Rica", "Cuento", 772),
 ("ae-*", "alfredo-espino", "Alfredo Espino", "El Salvador", "Poesía", 773),
 ("dr-*", "manuel-diaz-rodriguez", "Manuel Díaz Rodríguez", "Venezuela", "Novela", 774),
 ("ma-*", "manuel-a-alonso", "Manuel A. Alonso", "Puerto Rico", "Cuento", 775),
]

d = json.load(open("latam_sondeo.json"))
creados = 0
for patron, aslug, nombre, pais, genero, cid in SUELTAS:
    pref = patron.split("-")[0]
    obras = d[aslug]["piezas"] + d[aslug]["libros"]
    for i, (titulo, slug, n) in enumerate(obras):
        c = {"slug": slug, "titulo": titulo, "autor": nombre,
             "tipo": "verso" if genero == "Poesía" else "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": {"texto": FUENTE,
                        "url": f"https://www.textos.info/{aslug}/{slug}"},
             "catalogo_id": cid + i,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":"","pais":pais,"genero":genero,
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2","preliminares":True,
             "opciones":{"salto_por_capitulo":True}}
        if genero != "Poesía":
            c["opciones"]["hyphenation"] = "es"
        pathlib.Path(f"obras/{pref}-{slug[:16]}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"  {pref}-{slug[:16]}.json  {titulo[:34]:<36} {pais}")
        creados += 1

PRELIM = """eh-horaciokalibang eh-viajemaravilloso ad-brenda jb-donarramonaotros
rb-nocheraso rb-reybufon tc-ensaladapollos tc-historiachuchoni av-besoevans
av-circulomuerte av-tressenasdosases av-yerbasanta cp-cuentomarionetes
cp-cuentosmalevolos cp-granjablanca cp-leyendahachisch ig-floridainca
jc-incomprension jc-marujarosafrutac jc-olgacatalina jc-sacristan
eb-nochedormida""".split()
n = 0
for archivo in PRELIM:
    p = pathlib.Path(f"obras/{archivo}.json")
    if not p.exists():
        print(f"  (no existe {archivo})"); continue
    c = json.loads(p.read_text(encoding="utf-8"))
    c["preliminares"] = True
    c = {k: c[k] for k in ORDEN if k in c}
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n += 1
print(f"\n{creados} obras creadas | {n} con preliminares declarados")
