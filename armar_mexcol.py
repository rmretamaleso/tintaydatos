#!/usr/bin/env python3
"""Genera las configuraciones de Nervo, Gutiérrez Nájera y Vargas Vila.

Se corre desde Pag_web, con mexcol.json al lado. Deja fuera «Cuentos Frágiles»,
que ya está publicado.
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUT = {"amado-nervo": ("Amado Nervo", "México", "ne"),
       "manuel-gutierrez-najera": ("Manuel Gutiérrez Nájera", "México", "gn"),
       "jose-maria-vargas-vila": ("José María Vargas Vila", "Colombia", "vv")}
YA = {"cuentos-fragiles"}
ANIOS = {"cuentos-color-de-humo":1890, "por-donde-se-sube-al-cielo":1882,
         "aura-o-las-violetas":1887, "el-diamante-de-la-inquietud":1917,
         "el-diablo-desinteresado":1916, "una-mentira":1917, "amnesia":1918,
         "un-sueno":1917, "cronicas":1922}
GEN = {"cronicas":"Memoria/Crónica", "por-donde-se-sube-al-cielo":"Novela",
       "aura-o-las-violetas":"Novela", "el-diamante-de-la-inquietud":"Novela",
       "una-mentira":"Novela"}

def corto(slug, pref):
    s = unicodedata.normalize("NFKD", slug).encode("ascii","ignore").decode()
    p = [x for x in s.split("-") if x not in ("de","la","el","los","las","y","un","una","a","al","se")]
    return f"{pref}-{''.join(p)[:16]}"

d = json.load(open("mexcol.json"))
cid, hechos = 519, []
for aslug, dat in d.items():
    if aslug not in AUT or not dat["libros"] and not dat.get("huerfanos"):
        continue
    nombre, pais, pref = AUT[aslug]
    for titulo, slug, n in sorted(dat["libros"], key=lambda x: -x[2]):
        if slug in YA:
            continue
        c = {"slug": slug, "titulo": titulo, "autor": nombre, "tipo": "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}/{slug}"},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":str(ANIOS.get(slug,"")),"pais":pais,
                "genero":GEN.get(slug,"Cuento"),"tipo":"Dominio público",
                "puede_alojarse":"si"},
             "nivel_capitulo":"h2",
             "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
        if slug in ANIOS:
            c["anio"] = ANIOS[slug]
        nom = corto(slug, pref)
        pathlib.Path(f"obras/{nom}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((nom, titulo, cid)); cid += 1

    huerf = dat.get("huerfanos") or []
    if len(huerf) >= 3:
        c = {"slug": f"cuentos-dispersos-{pref}", "titulo": "Cuentos Dispersos",
             "autor": nombre, "tipo": "prosa", "autor_slug": aslug,
             "piezas_fuente": [f"{s}::{t}" for t, s in huerf], "orden": "alfabetico",
             "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}",
                        "nota": (f"Reúne los {len(huerf)} relatos que la fuente publica "
                                 f"sueltos y que no figuran en ninguno de los libros del "
                                 f"autor disponibles allí. Recopilación de Tinta y Datos.")},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":"Cuentos dispersos",
                "autor":nombre,"anio":"","pais":pais,"genero":"Cuento",
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2","esperados":{"capitulos":len(huerf)},
             "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
        nom = f"{pref}-dispersos"
        pathlib.Path(f"obras/{nom}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((nom, f"Cuentos Dispersos ({len(huerf)})", cid)); cid += 1

for n,t,i in hechos:
    print(f"  {n+'.json':<26} {t[:42]:<44} id={i}")
print(f"\n{len(hechos)} configuraciones, ids 519-{cid-1}")
