#!/usr/bin/env python3
"""Genera las configuraciones de las obras latinoamericanas de Gutenberg.

Se corre desde Pag_web. Cada .json solo necesita el número del libro: el
adaptador consulta la ficha y arma el colofón con la edición impresa original.

Quedan fuera José Rizal (filipino), «Argentina, Legend and History» (en inglés)
y el estatuto de la Liga Filipina (documento administrativo).
"""
import json, pathlib

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
OBRAS = [
 # id, archivo, título, autor, país, año, género
 (23035,"oc-quilito","Quilito","Carlos María Ocantos","Argentina",1891,"Novela"),
 (63424,"lv-cuentoschile","Cuentos Populares en Chile","Ramón A. Laval","Chile",1923,"Cuento"),
 (69164,"lv-cuentosnuncaacabar","Cuentos Chilenos de Nunca Acabar","Ramón A. Laval","Chile",1925,"Cuento"),
 (77353,"ct-instruccionpr","Historia de la Instrucción Pública en Puerto Rico","Cayetano Coll y Toste","Puerto Rico",1910,"Ensayo"),
 (73179,"ct-colonpr","Colón en Puerto Rico","Cayetano Coll y Toste","Puerto Rico",1893,"Ensayo"),
 (49354,"gp-viajeeeuui","Viaje a los Estados Unidos, tomo I","Guillermo Prieto","México",1877,"Memoria/Crónica"),
 (56519,"gp-viajeeeuuii","Viaje a los Estados Unidos, tomo II","Guillermo Prieto","México",1877,"Memoria/Crónica"),
 (58910,"gp-viajeeeuuiii","Viaje a los Estados Unidos, tomo III","Guillermo Prieto","México",1878,"Memoria/Crónica"),
 (47346,"fv-escritospoliticos","Escritos Políticos, Económicos y Literarios","Florencio Varela","Argentina",1859,"Ensayo"),
 (49376,"pg-platan","Del Plata al Niágara","Paul Groussac","Argentina",1897,"Memoria/Crónica"),
 (41575,"mc-juvenilia","Juvenilia","Miguel Cané","Argentina",1884,"Memoria/Crónica"),
 (29014,"mc-enviaje","En Viaje (1881-1882)","Miguel Cané","Argentina",1884,"Memoria/Crónica"),
 (63600,"lm-ranquelesi","Una Excursión a los Indios Ranqueles, tomo I","Lucio V. Mansilla","Argentina",1870,"Memoria/Crónica"),
 (63767,"lm-ranquelesii","Una Excursión a los Indios Ranqueles, tomo II","Lucio V. Mansilla","Argentina",1870,"Memoria/Crónica"),
 (73064,"eh-moralsocial","Moral Social","Eugenio María de Hostos","Puerto Rico",1888,"Ensayo"),
 (31724,"ll-granaldea","La Gran Aldea","Lucio Vicente López","Argentina",1884,"Novela"),
 (63378,"lu-corazonjuglar","El Corazón Juglar","Luis G. Urbina","México",1920,"Poesía"),
 (63587,"lu-estampasviaje","Estampas de Viaje","Luis G. Urbina","México",1920,"Memoria/Crónica"),
 (35407,"bm-rimas","Rimas","Bartolomé Mitre","Argentina",1854,"Poesía"),
 (63823,"al-nuevaspoesias","Nuevas Poesías y Evangélicas","Almafuerte","Argentina",1918,"Poesía"),
 (47184,"fj-antologiapr","Antología Portorriqueña","Manuel Fernández Juncos","Puerto Rico",1913,"Cuento"),
 (12368,"mg-contigopan","Contigo Pan y Cebolla","Manuel Eduardo de Gorostiza","México",1833,"Teatro"),
 (49359,"va-campesinopr","El Campesino Puertorriqueño","Francisco del Valle Atiles","Puerto Rico",1887,"Ensayo"),
 (70064,"gm-estudiosamerica","Estudios Americanos","Martín García Mérou","Argentina",1900,"Ensayo"),
 (43401,"sg-florpiel","A Flor de Piel","Gustavo Sánchez Galarraga","Cuba",1919,"Poesía"),
 (42321,"sb-loquedicehistoria","Lo Que Dice la Historia","Salvador Brau","Puerto Rico",1893,"Ensayo"),
 (41853,"sb-rafaelcordero","Rafael Cordero: Elogio Póstumo","Salvador Brau","Puerto Rico",1891,"Ensayo"),
 (45151,"pg2-conquistahabana","Historia de la Conquista de la Habana (1762)","Pedro José Guiteras","Cuba",1856,"Ensayo"),
 (45180,"fc2-poetascolor","Poetas de Color","Francisco Calcagno","Cuba",1878,"Ensayo"),
]
VERSO = {"Poesía"}
cid = 951
for libro, archivo, titulo, autor, pais, anio, genero in OBRAS:
    c = {"slug": archivo.split("-", 1)[1], "titulo": titulo, "autor": autor,
         "anio": anio, "tipo": "verso" if genero in VERSO else "prosa",
         "gutenberg": libro,
         "catalogo": CAT,
         "fuente": {},          # lo completa el adaptador con la edición original
         "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Literatura","titulo":titulo,"autor":autor,
            "anio":str(anio),"pais":pais,"genero":genero,
            "tipo":"Dominio público","puede_alojarse":"si"},
         "nivel_capitulo":"h2","opciones":{"salto_por_capitulo":True}}
    if genero not in VERSO:
        c["opciones"]["hyphenation"] = "es"
    pathlib.Path(f"obras/{archivo}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"  {archivo+'.json':<26} {titulo[:38]:<40} {pais:<12} id={cid}")
    cid += 1
from collections import Counter
print(f"\n{len(OBRAS)} configuraciones, ids 951-{cid-1}")
print(dict(Counter(o[4] for o in OBRAS)))
