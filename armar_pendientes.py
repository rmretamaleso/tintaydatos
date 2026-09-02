#!/usr/bin/env python3
"""Genera las configuraciones de Galdós, Bécquer, Rosalía de Castro y Zayas.

Se corre desde Pag_web, con pendientes_sondeo.json al lado. Excluye lo ya
publicado. Los años que no constan quedan vacíos; fijar_anios.py los marca.
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUT = {"benito-perez-galdos": ("Benito Pérez Galdós", "España", "pg"),
       "gustavo-adolfo-becquer": ("Gustavo Adolfo Bécquer", "España", "be"),
       "rosalia-de-castro": ("Rosalía de Castro", "España", "rc"),
       "maria-de-zayas-y-sotomayor": ("María de Zayas y Sotomayor", "España", "mz")}
YA = {"fortunata-y-jacinta", "rimas", "en-las-orillas-del-sar", "la-hija-del-mar"}

ANIOS = {
 # Galdós — novelas contemporáneas
 "la-fontana-de-oro":1870,"dona-perfecta":1876,"gloria":1877,
 "la-familia-de-leon-roch":1878,"la-desheredada":1881,"el-amigo-manso":1882,
 "el-doctor-centeno":1883,"tormento":1884,"la-de-bringas":1884,
 "lo-prohibido":1885,"miau":1888,"la-incognita":1889,"realidad":1889,
 "angel-guerra":1891,"tristana":1892,"nazarin":1895,"halma":1895,
 "misericordia":1897,"el-abuelo":1897,"casandra":1905,"el-audaz":1871,
 "marianela":1878,"torquemada-en-la-hoguera":1889,
 "torquemada-en-el-purgatorio":1894,"torquemada-y-san-pedro":1895,
 # teatro
 "electra":1901,"la-loca-de-la-casa":1893,"la-de-san-quintin":1894,
 "la-razon-de-la-sinrazon":1915,
 # Bécquer
 "cartas-desde-mi-celda":1864,"cartas-literarias-a-una-mujer":1861,
 "el-caudillo-de-las-manos-rojas":1858,"el-monte-de-las-animas":1861,
 "maese-perez-el-organista":1861,"la-rosa-de-pasion":1864,"el-gnomo":1863,
 "la-promesa":1863,"creed-en-dios":1862,"la-creacion":1861,
 # Rosalía
 "la-flor":1857,"a-mi-madre":1863,"flavio":1861,
 "el-caballero-de-las-botas-azules":1867,"el-primer-loco":1881,
 # Zayas
 "novelas-amorosas-y-ejemplares":1637,"desenganos-amorosos":1647,
}
TEATRO = {"electra","la-loca-de-la-casa","la-de-san-quintin","realidad",
 "la-razon-de-la-sinrazon","el-abuelo","casandra","alma-y-vida","barbara",
 "amor-y-ciencia","mariucha","pedro-minio","celia-en-los-infiernos",
 "alceste","sor-simona","el-tacano-salomon","santa-juana-de-castilla",
 "los-condenados","voluntad","la-fiera","antonio-canovas"}
POESIA = {"a-mi-madre","la-flor","follas-novas","cantares-gallegos"}
CRONICA = {"cartas-desde-mi-celda","cartas-literarias-a-una-mujer",
 "la-estafeta-romantica","memorias-de-un-desmemoriado"}

def corto(slug, pref):
    s = unicodedata.normalize("NFKD", slug).encode("ascii","ignore").decode()
    p = [x for x in s.split("-") if x not in ("de","la","el","los","las","y","un","una","a","al","en","del")]
    return f"{pref}-{''.join(p)[:16]}"

d = json.load(open("pendientes_sondeo.json"))
cid, hechos, usados = 530, [], set()
for aslug, dat in d.items():
    nombre, pais, pref = AUT[aslug]
    for titulo, slug, n in sorted(dat["libros"], key=lambda x: -x[2]):
        if slug in YA:
            continue
        genero = ("Teatro" if slug in TEATRO else "Poesía" if slug in POESIA
                  else "Memoria/Crónica" if slug in CRONICA
                  else "Novela" if n > 8 else "Cuento")
        c = {"slug": slug, "titulo": titulo, "autor": nombre, "tipo": "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}/{slug}"},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":str(ANIOS.get(slug,"")),"pais":pais,"genero":genero,
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2",
             "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
        if slug in ANIOS:
            c["anio"] = ANIOS[slug]
        nom = corto(slug, pref)
        while nom in usados:
            nom += "x"
        usados.add(nom)
        pathlib.Path(f"obras/{nom}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((nom, titulo, cid, genero)); cid += 1

    huerf = dat.get("huerfanos") or []
    if len(huerf) >= 3:
        c = {"slug": f"cuentos-dispersos-{pref}", "titulo": "Cuentos y Prosas Dispersos",
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
        hechos.append((f"{pref}-dispersos", f"Dispersos ({len(huerf)})", cid, "Cuento"))
        cid += 1

for n,t,i,g in hechos:
    print(f"  {n+'.json':<24} {t[:36]:<38} {g:<16} id={i}")
print(f"\n{len(hechos)} configuraciones, ids 530-{cid-1}")
