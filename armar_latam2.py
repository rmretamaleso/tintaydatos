#!/usr/bin/env python3
"""Genera las configuraciones de la segunda tanda latinoamericana.

Se corre desde Pag_web, con latam2_sondeo.json al lado.

Descarta «Todos los Cuentos» de Arlt —recopilación que engloba cuatro libros
suyos y sus relatos sueltos— y la copia repetida de «Nuevas Aguafuertes».
"""
import json, pathlib, re, unicodedata

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
FUENTE = "textos.info — edición de Edu Robsy, marcada como dominio público"
AUT = {
 "roberto-arlt": ("Roberto Arlt","Argentina","ar"),
 "jose-seferino-alvarez-fray-mocho": ("José Seferino Álvarez «Fray Mocho»","Argentina","fm"),
 "rosa-guerra": ("Rosa Guerra","Argentina","rg"),
 "juan-cortada": ("Juan Cortada","Argentina","jt"),
 "domingo-arena": ("Domingo Arena","Uruguay","da"),
 "teresa-wilms-montt": ("Teresa Wilms Montt","Chile","tw"),
 "vicente-riva-palacio": ("Vicente Riva Palacio","México","rp"),
 "rafael-delgado": ("Rafael Delgado","México","rd"),
 "xavier-villaurrutia": ("Xavier Villaurrutia","México","xv"),
 "francisco-javier-alegre": ("Francisco Javier Alegre","México","fa"),
 "pablo-palacio": ("Pablo Palacio","Ecuador","pp"),
 "rufino-blanco-fombona": ("Rufino Blanco Fombona","Venezuela","bf"),
 "luis-bonafoux-quintero": ("Luis Bonafoux Quintero","Puerto Rico","lb"),
 "martin-del-barco-centenera": ("Martín del Barco Centenera","Argentina","bt"),
}
FUERA = {"todos-los-cuentos", "nuevas-aguafuertes-2"}
ANIOS = {"el-juguete-rabioso":1926,"los-siete-locos":1929,"los-lanzallamas":1931,
 "el-amor-brujo":1932,"aguafuertes-portenas":1933,"aguafuertes-cariocas":1997,
 "trescientos-millones":1932,"lucia-miranda":1860,"inquietudes-sentimentales":1917,
 "monja-y-casada-virgen-y-martir":1868,"martin-garatuza":1868,
 "los-piratas-del-golfo":1869,"calvario-y-tabor":1868,"la-vuelta-de-los-muertos":1870,
 "los-cuentos-del-general":1896,"la-calandria":1890,"angelina":1893,
 "los-parientes-ricos":1903,"un-hombre-muerto-a-puntapies-cuentos":1927,
 "debora":1927,"vida-del-ahorcado":1932,
 "la-argentina-y-la-conquista-del-rio-de-la-plata":1602}
NOVELA = {"el-juguete-rabioso","los-siete-locos","los-lanzallamas","el-amor-brujo",
 "lucia-miranda","monja-y-casada-virgen-y-martir","martin-garatuza",
 "los-piratas-del-golfo","calvario-y-tabor","la-vuelta-de-los-muertos",
 "las-dos-emparedadas","memorias-de-un-impostor","la-calandria","angelina",
 "los-parientes-ricos","vida-del-ahorcado","debora","memorias-de-un-vigilante"}
CRONICA = {"aguafuertes-portenas","aguafuertes-cariocas","nuevas-aguafuertes",
 "viaje-a-la-isla-de-mallorca-en-el-estio-de-1845","huellas-literarias",
 "historia-de-la-compania-de-jesus-en-nueva-espana"}
TEATRO = {"trescientos-millones","comedia-inmortal"}
VERSO = {"la-argentina-y-la-conquista-del-rio-de-la-plata"}

def corto(slug, pref):
    s = unicodedata.normalize("NFKD", slug).encode("ascii","ignore").decode()
    p = [x for x in s.split("-") if x not in ("de","la","el","los","las","y","un","una","a","al","del","en")]
    return f"{pref}-{''.join(p)[:16]}"

d = json.load(open("latam2_sondeo.json"))
cid, hechos, usados = 776, [], set()
for aslug, dat in d.items():
    if aslug not in AUT: continue
    nombre, pais, pref = AUT[aslug]
    dentro = {s for _, s in dat.get("duplicados", [])}
    todos = dat["libros"] + [(t, s, 0) for t, s, _ in dat["piezas"]
                             if not dat["libros"]]     # autores de una sola pieza
    for titulo, slug, n in sorted(todos, key=lambda x: -x[2]):
        if slug in FUERA or slug in dentro: continue
        genero = ("Poesía" if slug in VERSO else "Teatro" if slug in TEATRO
                  else "Memoria/Crónica" if slug in CRONICA
                  else "Novela" if slug in NOVELA else "Cuento")
        c = {"slug": slug, "titulo": titulo, "autor": nombre,
             "tipo": "verso" if slug in VERSO else "prosa",
             "url": f"https://www.textos.info/{aslug}/{slug}/ebook", "catalogo": CAT,
             "fuente": {"texto": FUENTE, "url": f"https://www.textos.info/{aslug}/{slug}"},
             "catalogo_id": cid,
             "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":nombre,
                "anio":str(ANIOS.get(slug,"")),"pais":pais,"genero":genero,
                "tipo":"Dominio público","puede_alojarse":"si"},
             "nivel_capitulo":"h2", "opciones":{"salto_por_capitulo":True}}
        if slug not in VERSO: c["opciones"]["hyphenation"] = "es"
        if n == 0: c["preliminares"] = True
        if slug in ANIOS: c["anio"] = ANIOS[slug]
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
print(f"\n{len(hechos)} configuraciones, ids 776-{cid-1}")
print(dict(Counter(p for _,_,p,_ in hechos)))
