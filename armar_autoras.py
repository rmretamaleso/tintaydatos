#!/usr/bin/env python3
"""Genera las configuraciones de las cuatro autoras a partir de autoras.json.

Se corre una sola vez, desde Pag_web y con autoras.json al lado:

    python3 armar_autoras.py

Deja fuera los libros ya publicados y «El Corazón de la Mujer», que está
contenido en «Novelas y Cuadros de la Vida Sur-Americana».
Los años que no constan quedan vacíos: no se inventan.
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUTORAS = {
 "carmen-de-burgos": ("Carmen de Burgos", "España", "bu"),
 "fernan-caballero": ("Fernán Caballero", "España", "fc"),
 "juana-manuela-gorriti": ("Juana Manuela Gorriti", "Argentina", "go"),
 "soledad-acosta-de-samper": ("Soledad Acosta de Samper", "Colombia", "sa"),
}
YA = {"la-rampa","la-malcasada","la-gaviota","clemencia",
      "novelas-y-cuadros-de-la-vida-sur-americana"}
FUERA = {"el-corazon-de-la-mujer"}          # contenido en Novelas y Cuadros
ANIOS = {"la-gaviota":1849,"clemencia":1852,"la-familia-de-alvareda":1856,
 "lagrimas":1839,"la-estrella-de-vandalia":1855,"una-en-otra":1849,
 "un-servilon-y-un-liberalito":1857,"la-mitologia-contada-a-los-ninos-e-historia-de-los-grandes-hombres-de-la-grecia":1867,
 "los-inadaptados":1909,"la-rampa":1917,"la-malcasada":1923,"quiero-vivir-mi-vida":1931,
 "los-anticuarios":1919,"el-ultimo-deseo":1916,"puñal-de-claveles":1931,
 "la-quena":1845,"el-pozo-del-yocci":1869,"oasis-en-la-vida":1888,
 "los-piratas-en-cartagena":1886,"teresa-la-limena":1869}
NOVELA = {"la-gaviota","clemencia","la-familia-de-alvareda","lagrimas","la-rampa",
 "la-malcasada","los-inadaptados","quiero-vivir-mi-vida","los-anticuarios",
 "oasis-en-la-vida","teresa-la-limena","la-quena","amadis","confidencias",
 "la-estrella-de-vandalia","una-en-otra","los-piratas-en-cartagena"}

def slugcorto(s, pref):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    s = re.sub(r"[^a-z0-9-]", "", s.lower())
    partes = [p for p in s.split("-") if p not in ("de","la","el","los","las","y","un","una","a")]
    return f"{pref}-{''.join(partes)[:18]}"

d = json.load(open("autoras.json"))
cid, hechos = 389, []
for aslug, dat in d.items():
    nombre, pais, pref = AUTORAS[aslug]
    for titulo, slug, n in sorted(dat["libros"], key=lambda x: -x[2]):
        if slug in YA or slug in FUERA:
            continue
        c = {"slug": slug, "titulo": titulo, "autor": nombre, "tipo": "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}/{slug}"},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":str(ANIOS.get(slug,"")),"pais":pais,
                "genero":"Novela" if slug in NOVELA else "Cuento",
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2",
             "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
        if slug in ANIOS:
            c["anio"] = ANIOS[slug]
        nom = slugcorto(slug, pref)
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
                                 f"sueltos y que no figuran en ninguno de los libros de "
                                 f"la autora disponibles allí. Recopilación de Tinta y Datos.")},
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
print(f"\n{len(hechos)} configuraciones, ids 389-{cid-1}")
