#!/usr/bin/env python3
"""Genera las configuraciones de los 36 autores latinoamericanos.

Se corre desde Pag_web, con latam_sondeo.json al lado.

Descarta «Todos los Cuentos» de José de la Cuadra —recopilación que engloba sus
libros— y los volúmenes contenidos en otros. Los años que no constan quedan
vacíos; fijar_anios.py los marca «s. f.».
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"

AUT = {
 "estanislao-del-campo": ("Estanislao del Campo","Argentina","ec"),
 "eduardo-gutierrez": ("Eduardo Gutiérrez","Argentina","eg"),
 "eduardo-ladislao-holmberg": ("Eduardo Ladislao Holmberg","Argentina","eh"),
 "carlos-octavio-bunge": ("Carlos Octavio Bunge","Argentina","cb"),
 "jose-ingenieros": ("José Ingenieros","Argentina","ji"),
 "juan-bautista-alberdi": ("Juan Bautista Alberdi","Argentina","ja"),
 "jose-marmol": ("José Mármol","Argentina","jm"),
 "juan-antonio-argerich": ("Juan Antonio Argerich","Argentina","jr"),
 "carlos-alberto-leumann": ("Carlos Alberto Leumann","Argentina","cl"),
 "eduardo-acevedo-diaz": ("Eduardo Acevedo Díaz","Uruguay","ad"),
 "carlos-reyles": ("Carlos Reyles","Uruguay","cr"),
 "jose-alonso-y-trelles": ("José Alonso y Trelles","Uruguay","at"),
 "jose-pedro-bellan": ("José Pedro Bellán","Uruguay","jb"),
 "jose-joaquin-fernandez-de-lizardi": ("José Joaquín Fernández de Lizardi","México","fl"),
 "emilio-rabasa": ("Emilio Rabasa","México","er"),
 "laura-mendez-de-cuenca": ("Laura Méndez de Cuenca","México","lm"),
 "jose-maria-roa-barcena": ("José María Roa Bárcena","México","rb"),
 "jose-tomas-de-cuellar": ("José Tomás de Cuéllar","México","tc"),
 "juan-antonio-mateos": ("Juan Antonio Mateos","México","am"),
 "juan-diaz-covarrubias": ("Juan Díaz Covarrubias","México","dc"),
 "ireneo-paz-flores": ("Ireneo Paz","México","ip"),
 "juan-ruiz-de-alarcon": ("Juan Ruiz de Alarcón","México","ra"),
 "abraham-valdelomar": ("Abraham Valdelomar","Perú","av"),
 "clemente-palma": ("Clemente Palma","Perú","cp"),
 "luis-benjamin-cisneros": ("Luis Benjamín Cisneros","Perú","bc"),
 "inca-garcilaso-de-la-vega": ("Inca Garcilaso de la Vega","Perú","ig"),
 "alberto-del-solar": ("Alberto del Solar","Chile","as"),
 "carlos-gagini": ("Carlos Gagini","Costa Rica","cg"),
 "manuel-gonzalez-zeledon": ("Manuel González Zeledón","Costa Rica","gz"),
 "alfredo-espino": ("Alfredo Espino","El Salvador","ae"),
 "arturo-ambrogi": ("Arturo Ambrogi","El Salvador","aa"),
 "manuel-diaz-rodriguez": ("Manuel Díaz Rodríguez","Venezuela","dr"),
 "francisco-campos-coello": ("Francisco Campos Coello","Ecuador","fc"),
 "jose-de-la-cuadra": ("José de la Cuadra","Ecuador","jc"),
 "emilio-bobadilla": ("Emilio Bobadilla","Cuba","eb"),
 "manuel-a-alonso": ("Manuel A. Alonso","Puerto Rico","ma"),
}
FUERA = {"todos-los-cuentos", "idealismos"}
ANIOS = {"fausto":1866,"amalia":1851,"juan-moreira":1879,
 "el-periquillo-sarniento":1816,"la-bola":1887,"el-caballero-carmelo":1918,
 "cuentos-malevolos":1904,"los-sangurimas":1934,"horno":1932,
 "el-jibaro":1849,"comentarios-reales":1609,"la-verdad-sospechosa":1634,
 "las-fuerzas-extranas":1906,"sangre-patricia":1902,"idolos-rotos":1901,
 "jicotencal":1826,"soledad":1894,"beba":1894,"el-embrujo-de-sevilla":1922}
VERSO = {"fausto","jicoténcal"}

def corto(slug, pref):
    s = unicodedata.normalize("NFKD", slug).encode("ascii","ignore").decode()
    p = [x for x in s.split("-") if x not in ("de","la","el","los","las","y","un","una","a","al","del","en")]
    return f"{pref}-{''.join(p)[:16]}"

d = json.load(open("latam_sondeo.json"))
cid, hechos, usados = 683, [], set()
for aslug, dat in d.items():
    if aslug not in AUT:
        continue
    nombre, pais, pref = AUT[aslug]
    dentro = {s for _, s in dat.get("duplicados", [])}
    for titulo, slug, n in sorted(dat["libros"], key=lambda x: -x[2]):
        if slug in FUERA or slug in dentro:
            continue
        c = {"slug": slug, "titulo": titulo, "autor": nombre,
             "tipo": "verso" if slug in VERSO else "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}/{slug}"},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":str(ANIOS.get(slug,"")),"pais":pais,
                "genero":"Poesía" if slug in VERSO else ("Novela" if n > 8 else "Cuento"),
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2",
             "opciones":{"salto_por_capitulo":True}}
        if slug not in VERSO:
            c["opciones"]["hyphenation"] = "es"
        if slug in ANIOS:
            c["anio"] = ANIOS[slug]
        nom = corto(slug, pref)
        while nom in usados: nom += "x"
        usados.add(nom)
        pathlib.Path(f"obras/{nom}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((nom, titulo, pais, cid)); cid += 1

    huerf = dat.get("huerfanos") or []
    if len(huerf) >= 3:
        c = {"slug": f"dispersos-{pref}", "titulo": "Cuentos y Prosas Dispersos",
             "autor": nombre, "tipo": "prosa", "autor_slug": aslug,
             "piezas_fuente": [f"{s}::{t}" for t, s in huerf], "orden": "alfabetico",
             "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}",
                        "nota": (f"Reúne los {len(huerf)} textos que la fuente publica "
                                 f"sueltos y que no figuran en ninguno de los libros del "
                                 f"autor disponibles allí. Recopilación de Tinta y Datos.")},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":"Cuentos y prosas dispersos",
                "autor":nombre,"anio":"","pais":pais,"genero":"Cuento",
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2","esperados":{"capitulos":len(huerf)},
             "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
        pathlib.Path(f"obras/{pref}-dispersos.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((f"{pref}-dispersos", f"Dispersos ({len(huerf)})", pais, cid))
        cid += 1

from collections import Counter
for n,t,p,i in hechos:
    print(f"  {n+'.json':<24} {t[:34]:<36} {p:<12} id={i}")
print(f"\n{len(hechos)} configuraciones, ids 683-{cid-1}")
print(dict(Counter(p for _,_,p,_ in hechos)))
