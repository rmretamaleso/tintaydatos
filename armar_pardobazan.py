#!/usr/bin/env python3
"""Genera las configuraciones de Emilia Pardo Bazán.

Se corre desde Pag_web, con pardobazan.json al lado.

Descarta «Cuentos», que no es un libro suyo sino una recopilación de la fuente:
reúne los 570 relatos que ella publicó en doce volúmenes distintos entre 1885 y
1922. Se prefieren esos volúmenes, que son los que compuso ella.
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUTORA = "Emilia Pardo Bazán"
YA = {"los-pazos-de-ulloa", "la-madre-naturaleza", "la-quimera", "la-tribuna"}
FUERA = {"cuentos"}          # recopilación de la fuente, no libro de la autora

ANIOS = {
 "pascual-lopez":1879,"un-viaje-de-novios":1881,"la-tribuna":1883,
 "el-cisne-de-vilamorta":1885,"la-dama-joven":1885,"los-pazos-de-ulloa":1886,
 "la-madre-naturaleza":1887,"insolacion":1889,"morrina":1889,
 "insolacion-y-morrina":1889,"una-cristiana":1890,"la-prueba":1890,
 "la-piedra-angular":1891,"cuentos-de-marineda":1892,"dona-milagros":1894,
 "memorias-de-un-solteron-adan-y-eva":1896,"el-tesoro-de-gaston":1897,
 "el-saludo-de-las-brujas":1898,"cuentos-de-amor":1898,
 "cuentos-sacroprofanos":1899,"misterio":1903,"la-quimera":1905,
 "la-sirena-negra":1908,"dulce-sueno":1911,"cuentos-tragicos":1912,
 "cuentos-de-la-tierra":1922,"la-cuestion-palpitante":1883,
 "el-nino-de-guzman":1891,"cuentos-nuevos":1894,"cuentos-del-terruno":1907,
 "la-gota-de-sangre":1911,"cuentos-antiguos":1900,"cuentos-dramaticos":1909,
 "cuentos-de-navidad-y-reyes":1902,"cuentos-de-la-patria":1902,
 "cuentos-de-navidad-y-ano-nuevo":1914,"la-ultima-fada":1916,
}
NOVELA = {"pascual-lopez","un-viaje-de-novios","el-cisne-de-vilamorta",
 "insolacion","morrina","insolacion-y-morrina","una-cristiana","la-prueba",
 "la-piedra-angular","dona-milagros","memorias-de-un-solteron-adan-y-eva",
 "el-tesoro-de-gaston","el-saludo-de-las-brujas","misterio","la-sirena-negra",
 "dulce-sueno","el-nino-de-guzman","la-gota-de-sangre","la-dama-joven",
 "la-ultima-fada","bucolica","en-las-cavernas"}
ENSAYO = {"la-cuestion-palpitante"}

def corto(slug):
    s = unicodedata.normalize("NFKD", slug).encode("ascii","ignore").decode()
    p = [x for x in s.split("-") if x not in ("de","la","el","los","las","y","un","una","a","al","del","en")]
    return f"pb-{''.join(p)[:18]}"

d = json.load(open("pardobazan.json"))
cid, hechos, usados = 645, [], set()
for titulo, slug, n in sorted(d["libros"], key=lambda x: -x[2]):
    if slug in YA or slug in FUERA:
        continue
    genero = ("Ensayo" if slug in ENSAYO else
              "Novela" if slug in NOVELA else "Cuento")
    c = {"slug": slug, "titulo": titulo, "autor": AUTORA, "tipo": "prosa",
         "url": f"https://www.textos.info/emilia-pardo-bazan/{slug}/ebook",
         "catalogo": CAT,
         "fuente": {"texto": FUENTE,
                    "url": f"https://www.textos.info/emilia-pardo-bazan/{slug}"},
         "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":AUTORA,
            "anio":str(ANIOS.get(slug,"")),"pais":"España","genero":genero,
            "tipo":"Dominio público","puede_alojarse":"si"},
         "nivel_capitulo":"h2",
         "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
    if slug in ANIOS:
        c["anio"] = ANIOS[slug]
    nom = corto(slug)
    while nom in usados:
        nom += "x"
    usados.add(nom)
    pathlib.Path(f"obras/{nom}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    hechos.append((nom, titulo, cid, genero)); cid += 1

for n,t,i,g in hechos:
    print(f"  {n+'.json':<26} {t[:38]:<40} {g:<8} id={i}")
print(f"\n{len(hechos)} configuraciones, ids 645-{cid-1}")
print("Descartado «Cuentos»: es recopilación de la fuente, no libro de la autora.")
