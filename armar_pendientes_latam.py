#!/usr/bin/env python3
"""Completa la obra de cinco autores latinoamericanos ya publicados.

Se corre desde Pag_web, con pendientes_latam.json al lado.

De Palma se toman «Tradiciones Peruanas» y «Las Mejores Tradiciones Peruanas»
—que no contienen las series I a III ya publicadas, sino otras tradiciones—
declarando en el colofón que la selección es de la fuente. Se descartan las
tradiciones sueltas que ya están dentro de esos volúmenes.
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUT = {"ricardo-palma": ("Ricardo Palma","Perú","pa"),
       "gertrudis-gomez-de-avellaneda": ("Gertrudis Gómez de Avellaneda","Cuba","ga"),
       "cesar-vallejo": ("César Vallejo","Perú","cv"),
       "domingo-faustino-sarmiento": ("Domingo F. Sarmiento","Argentina","sa"),
       "clorinda-matto-de-turner": ("Clorinda Matto de Turner","Perú","mt")}
YA = {"tradiciones-peruanas-i","tradiciones-peruanas-ii","tradiciones-peruanas-iii",
      "sab","dos-mujeres","el-tungsteno","paco-yunque","facundo",
      "recuerdos-de-provincia","aves-sin-nido","rudamente-pulidamente-manosamente"}
ANIOS = {"guatimozin-ultimo-emperador-de-mejico":1846,"el-artista-barquero":1861,
 "espatolino":1844,"dolores":1851,"escalas":1923,"fabla-salvaje":1923,
 "rusia-en-1931":1931,"contra-el-secreto-profesional":1973,
 "el-arte-y-la-revolucion":1973,"hacia-el-reino-de-los-sciris":1967,
 "estados-unidos":1847,"cuatro-conferencias-sobre-america-del-sur":1909,
 "tradiciones-en-salsa-verde":1901,"corona-patriotica":1853}
NOVELA = {"guatimozin-ultimo-emperador-de-mejico","el-artista-barquero","espatolino",
 "dolores","la-velada-del-helecho","fabla-salvaje","hacia-el-reino-de-los-sciris"}
ENSAYO = {"el-arte-y-la-revolucion","contra-el-secreto-profesional","rusia-en-1931",
 "estados-unidos","cuatro-conferencias-sobre-america-del-sur"}
VERSO = {"corona-patriotica"}
# antologías de la fuente: se publican, pero declarándolo
ANTOLOGIAS = {"tradiciones-peruanas","las-mejores-tradiciones-peruanas"}

def corto(slug, pref):
    s = unicodedata.normalize("NFKD", slug).encode("ascii","ignore").decode()
    p = [x for x in s.split("-") if x not in ("de","la","el","los","las","y","un","una","a","al","del","en","que","con")]
    return f"{pref}-{''.join(p)[:16]}"

d = json.load(open("pendientes_latam.json"))
cid, hechos, usados = 900, [], set()
for aslug, dat in d.items():
    nombre, pais, pref = AUT[aslug]
    for titulo, slug, n in sorted(dat["libros"], key=lambda x: -x[2]):
        if slug in YA: continue
        genero = ("Poesía" if slug in VERSO else "Ensayo" if slug in ENSAYO
                  else "Novela" if slug in NOVELA else "Cuento")
        fuente = {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}/{slug}"}
        if slug in ANTOLOGIAS:
            fuente["nota"] = ("Selección de tradiciones hecha por la fuente, distinta "
                              "de las series que Palma publicó entre 1872 y 1910; Tinta "
                              "y Datos edita por separado las tres primeras series.")
        c = {"slug": slug, "titulo": titulo, "autor": nombre,
             "tipo": "verso" if slug in VERSO else "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": fuente, "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":str(ANIOS.get(slug,"")),"pais":pais,"genero":genero,
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2","opciones":{"salto_por_capitulo":True}}
        if slug not in VERSO: c["opciones"]["hyphenation"] = "es"
        if slug in ANIOS: c["anio"] = ANIOS[slug]
        nom = corto(slug, pref)
        while nom in usados: nom += "x"
        usados.add(nom)
        pathlib.Path(f"obras/{nom}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((nom, titulo, pais, cid)); cid += 1

    huerf = dat.get("huerfanos") or []
    if len(huerf) >= 3:
        c = {"slug": f"dispersos-{pref}", "titulo": "Prosas Dispersas",
             "autor": nombre, "tipo": "prosa", "autor_slug": aslug,
             "piezas_fuente": [f"{s}::{t}" for t, s in huerf], "orden": "alfabetico",
             "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}",
                        "nota": (f"Reúne los {len(huerf)} textos que la fuente publica "
                                 f"sueltos y que no figuran en ninguno de los libros del "
                                 f"autor disponibles allí. Recopilación de Tinta y Datos.")},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":"Prosas dispersas",
                "autor":nombre,"anio":"","pais":pais,"genero":"Cuento",
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2","esperados":{"capitulos":len(huerf)},
             "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
        pathlib.Path(f"obras/{pref}-dispersos.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((f"{pref}-dispersos", f"Dispersas ({len(huerf)})", pais, cid))
        cid += 1

for n,t,p,i in hechos:
    print(f"  {n+'.json':<24} {t[:36]:<38} {p:<10} id={i}")
print(f"\n{len(hechos)} configuraciones, ids 900-{cid-1}")
