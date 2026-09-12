#!/usr/bin/env python3
"""Añade los repositorios nacionales de acceso abierto de la región.

Segunda tanda del dominio «Revistas y repositorios»: los sistemas nacionales
que agregan la producción científica de cada país, y algunas bibliotecas
digitales patrimoniales.
"""
import csv, io
from ids import reservar

PORTALES = [
 # titulo, entidad, país, tema, url, nota
 ("Repositorio Nacional CONAHCYT",
  "Consejo Nacional de Humanidades, Ciencias y Tecnologías", "México",
  "Multidisciplinario", "https://repositorionacionalcti.mx/",
  "Reúne en acceso abierto tesis, artículos y datos de la investigación "
  "financiada con fondos públicos mexicanos."),
 ("SNRD — Sistema Nacional de Repositorios Digitales",
  "Ministerio de Ciencia, Tecnología e Innovación", "Argentina",
  "Multidisciplinario", "https://repositoriosdigitales.mincyt.gob.ar/",
  "Red argentina de repositorios institucionales, creada por la ley 26.899 "
  "que obliga a depositar en acceso abierto la investigación con fondos "
  "públicos."),
 ("SciELO Chile",
  "Programa de Información Científica, ANID", "Chile", "Multidisciplinario",
  "https://www.scielo.cl/",
  "Colección chilena de la red SciELO, con revistas científicas nacionales "
  "en texto completo."),
 ("SciELO México",
  "Universidad Nacional Autónoma de México", "México", "Multidisciplinario",
  "https://www.scielo.org.mx/",
  "Colección mexicana de la red SciELO."),
 ("SciELO Argentina",
  "CAICYT-CONICET", "Argentina", "Multidisciplinario",
  "https://www.scielo.org.ar/",
  "Colección argentina de la red SciELO."),
 ("SciELO Colombia",
  "Universidad Nacional de Colombia", "Colombia", "Multidisciplinario",
  "https://www.scielo.org.co/",
  "Colección colombiana de la red SciELO."),
 ("Memoria Chilena",
  "Biblioteca Nacional de Chile", "Chile", "Historia",
  "https://www.memoriachilena.gob.cl/",
  "Biblioteca digital patrimonial con libros, revistas y documentos sobre la "
  "cultura chilena. Muchos de sus fondos están declarados patrimonio cultural "
  "común, pero conviene comprobar la ficha de cada obra."),
 ("Biblioteca Digital Mundial",
  "UNESCO y Biblioteca del Congreso", "Regional", "Historia",
  "https://www.loc.gov/collections/world-digital-library/",
  "Manuscritos, mapas y libros raros de bibliotecas de todo el mundo, con "
  "fondo americano considerable y fichas en español."),
 ("Biblioteca Digital del Patrimonio Iberoamericano",
  "Asociación de Bibliotecas Nacionales de Iberoamérica", "Regional", "Historia",
  "https://www.iberoamericadigital.net/",
  "Reúne los fondos digitalizados de las bibliotecas nacionales "
  "iberoamericanas en un solo buscador."),
 ("Biblioteca Digital Hispánica",
  "Biblioteca Nacional de España", "España", "Historia",
  "https://bdh.bne.es/",
  "Fondo digitalizado de la Biblioteca Nacional de España, con abundante "
  "material americano de los siglos XVI al XIX."),
]

filas = list(csv.DictReader(open("catalogo.csv", encoding="utf-8")))
cols = list(filas[0].keys())
ya = {r["url"].rstrip("/") for r in filas}
nuevos = [p for p in PORTALES if p[4].rstrip("/") not in ya]
ids = reservar(len(nuevos))

for (titulo, entidad, pais, tema, url, nota), cid in zip(nuevos, ids):
    fila = {c: "" for c in cols}
    fila.update({"id": str(cid), "dominio": "Revistas y repositorios",
                 "titulo": titulo, "autor": entidad, "anio": "",
                 "pais": pais, "genero": tema, "tema": tema,
                 "tipo": "Acceso abierto", "fuente": entidad, "url": url,
                 "verificado": "True", "notas": nota, "puede_alojarse": "no"})
    filas.append(fila)
    print(f"  [{cid}] {titulo[:46]:<48} {pais:<12} {tema}")

o = io.StringIO()
w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
w.writeheader(); w.writerows(filas)
open("catalogo.csv", "w", encoding="utf-8").write(o.getvalue())
print(f"\n{len(nuevos)} añadidos | {len(PORTALES)-len(nuevos)} ya estaban")
