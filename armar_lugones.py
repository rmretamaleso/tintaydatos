#!/usr/bin/env python3
"""Genera las configuraciones de Lugones.

Los seis libros que la fuente publica como tales, más dos volúmenes:

  - «Las fuerzas extrañas» (1906), que la fuente solo tiene como relatos
    sueltos. No es una recopilación nuestra: es un libro que existe y que se
    reconstruye en el orden en que Lugones lo compuso.
  - los cuentos y prosas restantes, que sí van como dispersos.
"""
import json, pathlib

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUT, A = "Leopoldo Lugones", "leopoldo-lugones"

# orden del libro de 1906
FUERZAS = [
 ("la-fuerza-omega","La Fuerza Omega"), ("la-metamusica","La Metamúsica"),
 ("el-psychon","El Psychon"), ("un-fenomeno-inexplicable","Un Fenómeno Inexplicable"),
 ("la-lluvia-de-fuego","La Lluvia de Fuego"), ("la-estatua-de-sal","La Estatua de Sal"),
 ("los-caballos-de-abdera","Los Caballos de Abdera"),
 ("el-escuerzo","El Escuerzo"), ("el-milagro-de-san-wilfrido","El Milagro de San Wilfrido"),
 ("viola-acherontia","Viola Acherontia"), ("el-origen-del-diluvio","El Origen del Diluvio"),
 ("yzur","Yzur"),
]
ANIOS = {"el-angel-de-la-sombra":1926,"la-guerra-gaucha":1905,
         "el-imperio-jesuitico":1904,"los-ojos-de-la-reina":1927}
GEN = {"el-imperio-jesuitico":"Ensayo","el-angel-de-la-sombra":"Novela",
       "los-ojos-de-la-reina":"Novela"}
ABREV = {"el-angel-de-la-sombra":"angelsombra","la-guerra-gaucha":"guerragaucha",
 "los-ojos-de-la-reina":"ojosreina","el-imperio-jesuitico":"imperiojesuitico",
 "cuentos":"cuentos","el-punal":"punal"}

def escribir(nombre, c):
    pathlib.Path(f"obras/{nombre}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

d = json.load(open("lugones.json"))
cid, hechos = 511, []
for titulo, slug, n in sorted(d["libros"], key=lambda x: -x[2]):
    c = {"slug": slug, "titulo": titulo, "autor": AUT, "tipo": "prosa",
         "url": f"https://www.textos.info/{A}/{slug}/ebook", "catalogo": CAT,
         "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{A}/{slug}"},
         "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":AUT,
            "anio":str(ANIOS.get(slug,"")),"pais":"Argentina",
            "genero":GEN.get(slug,"Cuento"),"tipo":"Dominio público",
            "puede_alojarse":"si"},
         "nivel_capitulo":"h2",
         "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
    if slug in ANIOS:
        c["anio"] = ANIOS[slug]
    escribir(f"lu-{ABREV.get(slug, slug[:14])}", c)
    hechos.append((f"lu-{ABREV.get(slug, slug[:14])}", titulo, cid)); cid += 1

def volumen(nombre, slug, titulo, piezas, anio, nota, orden=None):
    global cid
    c = {"slug": slug, "titulo": titulo, "autor": AUT, "tipo": "prosa",
         "autor_slug": A, "piezas_fuente": [f"{s}::{t}" for s, t in piezas],
         "catalogo": CAT,
         "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{A}",
                    "nota": nota},
         "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":AUT,
            "anio":str(anio or ""),"pais":"Argentina","genero":"Cuento",
            "tipo":"Dominio público","puede_alojarse":"si"},
         "nivel_capitulo":"h2","esperados":{"capitulos":len(piezas)},
         "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
    if anio: c["anio"] = anio
    if orden: c["orden"] = orden
    escribir(nombre, c)
    hechos.append((nombre, f"{titulo} ({len(piezas)} textos)", cid)); cid += 1

volumen("lu-fuerzasextranas", "las-fuerzas-extranas", "Las Fuerzas Extrañas",
        FUERZAS, 1906,
        "La fuente publica estos doce relatos por separado, sin reunirlos en "
        "volumen. Esta edición reconstruye el libro que Lugones publicó en 1906, "
        "en el orden en que lo compuso.")

en_fuerzas = {s for s, _ in FUERZAS}
resto = [(s, t) for t, s in d["huerfanos"] if s not in en_fuerzas]
volumen("lu-dispersos", "cuentos-dispersos-lugones", "Cuentos Dispersos",
        resto, None,
        f"Reúne los {len(resto)} relatos y prosas de Lugones que la fuente "
        f"publica sueltos y que no figuran en ninguno de sus libros ni en «Las "
        f"fuerzas extrañas». Recopilación de Tinta y Datos.", orden="alfabetico")

for n, t, i in hechos:
    print(f"  {n+'.json':<26} {t[:44]:<46} id={i}")
print(f"\n{len(hechos)} configuraciones, ids 511-{cid-1}")
