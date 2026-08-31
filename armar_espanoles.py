#!/usr/bin/env python3
"""Genera las configuraciones de Valera, Valle-Inclán y Alarcón.

Se corre desde Pag_web, con espanoles.json al lado:

    python3 armar_espanoles.py

Descarta los libros que ya están contenidos en otros —los detectó la
comprobación de solapamiento— y los que ya están publicados. Los años que no
constan quedan vacíos; fijar_anios.py los marcará «s. f.».
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUT = {"juan-valera": ("Juan Valera", "va"),
       "ramon-maria-del-valle-inclan": ('Ramón María del Valle-Inclán', "vi"),
       "pedro-antonio-de-alarcon": ("Pedro Antonio de Alarcón", "al")}
YA = {"pepita-jimenez", "el-sombrero-de-tres-picos"}

ANIOS = {
 # Valera
 "pepita-jimenez":1874,"las-ilusiones-del-doctor-faustino":1875,"el-comendador-mendoza":1877,
 "dona-luz":1879,"pasarse-de-listo":1878,"juanita-la-larga":1895,"genio-y-figura":1897,
 "morsamor":1899,"cartas-americanas":1889,"nuevas-cartas-americanas":1890,
 "cuentos-y-chascarrillos-andaluces":1896,"asclepigenia":1878,"mariquita-y-antonio":1861,
 # Valle-Inclán
 "sonata-de-otono":1902,"sonata-de-estio":1903,"sonata-de-primavera":1904,
 "sonata-de-invierno":1905,"flor-de-santidad":1904,"aguila-de-blason":1907,
 "romance-de-lobos":1908,"cara-de-plata":1922,"los-cruzados-de-la-causa":1908,
 "el-resplandor-de-la-hoguera":1909,"gerifaltes-de-antano":1909,
 "la-lampara-maravillosa":1916,"la-media-noche":1917,"divinas-palabras":1920,
 "la-pipa-de-kif":1919,"tirano-banderas":1926,"la-corte-de-los-milagros":1927,
 "viva-mi-dueno":1928,"baza-de-espadas":1932,"martes-de-carnaval":1930,
 "jardin-umbrio":1903,"corte-de-amor":1903,"femeninas":1895,"la-cara-de-dios":1899,
 "comedias-barbaras":1907,"el-yermo-de-las-almas":1908,"el-marques-de-bradomin":1907,
 "cuento-de-abril":1910,"la-marquesa-rosalinda":1912,"el-embrujado":1913,
 "luces-de-bohemia":1920,"el-trueno-dorado":1936,
 # Alarcón
 "el-final-de-norma":1855,"el-sombrero-de-tres-picos":1874,"el-escandalo":1875,
 "el-nino-de-la-bola":1880,"el-capitan-veneno":1881,"la-prodiga":1882,
 "la-alpujarra":1874,"viajes-por-espana":1883,"historietas-nacionales":1881,
 "narraciones-inverosimiles":1882,"cuentos-amatorios":1881,"novelas-cortas":1881,
 "el-amigo-de-la-muerte":1852,"moros-y-cristianos":1881,"el-clavo":1853,
}
TEATRO = {"divinas-palabras","comedias-barbaras","aguila-de-blason","romance-de-lobos",
 "cara-de-plata","luces-de-bohemia","martes-de-carnaval","el-yermo-de-las-almas",
 "el-marques-de-bradomin","cuento-de-abril","la-marquesa-rosalinda","el-embrujado",
 "asclepigenia","tablado-de-marionetas-para-educacion-de-principes",
 "retablo-de-la-avaricia-la-lujuria-y-la-muerte"}
POESIA = {"la-pipa-de-kif","aromas-de-leyenda","el-pasajero"}
NOVELA = {"pepita-jimenez","dona-luz","juanita-la-larga","genio-y-figura","morsamor",
 "el-comendador-mendoza","pasarse-de-listo","mariquita-y-antonio","tirano-banderas",
 "la-corte-de-los-milagros","viva-mi-dueno","baza-de-espadas","flor-de-santidad",
 "los-cruzados-de-la-causa","el-resplandor-de-la-hoguera","gerifaltes-de-antano",
 "la-cara-de-dios","el-final-de-norma","el-escandalo","el-nino-de-la-bola",
 "el-capitan-veneno","la-prodiga","el-amigo-de-la-muerte","la-media-noche",
 "sonata-de-otono","sonata-de-estio","sonata-de-primavera","sonata-de-invierno"}
CRONICA = {"la-alpujarra","viajes-por-espana","cartas-americanas","nuevas-cartas-americanas",
 "a-vuela-pluma","la-lampara-maravillosa","algo-de-todo","el-ano-en-spitzberg"}

def nombre_archivo(slug, pref):
    s = unicodedata.normalize("NFKD", slug).encode("ascii","ignore").decode()
    p = [x for x in s.split("-") if x not in ("de","la","el","los","las","y","un","una","a","del")]
    return f"{pref}-{''.join(p)[:18]}"

d = json.load(open("espanoles.json"))
cid, hechos = 436, []
for aslug, dat in d.items():
    nombre, pref = AUT[aslug]
    dentro = {s for _, s in dat.get("duplicados", [])}
    for titulo, slug, n in sorted(dat["libros"], key=lambda x: -x[2]):
        if slug in YA or slug in dentro:
            continue
        genero = ("Teatro" if slug in TEATRO else "Poesía" if slug in POESIA
                  else "Novela" if slug in NOVELA
                  else "Memoria/Crónica" if slug in CRONICA else "Cuento")
        c = {"slug": slug, "titulo": titulo, "autor": nombre, "tipo": "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}/{slug}"},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":str(ANIOS.get(slug,"")),"pais":"España","genero":genero,
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2",
             "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
        if slug in ANIOS:
            c["anio"] = ANIOS[slug]
        nom = nombre_archivo(slug, pref)
        pathlib.Path(f"obras/{nom}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        hechos.append((nom, titulo, cid, genero)); cid += 1

for n,t,i,g in hechos:
    print(f"  {n+'.json':<28} {t[:36]:<38} {g:<16} id={i}")
print(f"\n{len(hechos)} configuraciones, ids 436-{cid-1}")
