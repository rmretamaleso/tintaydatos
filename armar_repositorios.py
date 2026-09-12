#!/usr/bin/env python3
"""Añade al catálogo los grandes portales de acceso abierto de la región.

No son obras sino puertas de entrada: sitios donde encontrar artículos, tesis y
libros de acceso abierto. Van al dominio «Revistas y repositorios», que existe
justamente para distinguirlos de las obras del catálogo.
"""
import csv, io
from ids import reservar

PORTALES = [
 # titulo, entidad, país, tema, url, nota
 ("SciELO — Scientific Electronic Library Online",
  "Red SciELO", "Regional", "Multidisciplinario",
  "https://www.scielo.org/",
  "Red iberoamericana de revistas científicas en texto completo y acceso "
  "abierto, en marcha desde 1998. Reúne colecciones nacionales de una docena "
  "de países."),
 ("Redalyc — Red de Revistas Científicas de América Latina y el Caribe",
  "Universidad Autónoma del Estado de México", "México", "Multidisciplinario",
  "https://www.redalyc.org/",
  "Sistema de indización y repositorio de revistas de la región, con énfasis "
  "en ciencias sociales y humanidades. Sin cargos para autores ni lectores."),
 ("La Referencia — Red Federada de Repositorios Institucionales",
  "LA Referencia", "Regional", "Multidisciplinario",
  "https://www.lareferencia.info/",
  "Red que federa los sistemas nacionales de repositorios de una decena de "
  "países, establecida en 2012. Permite buscar de una vez en todos ellos."),
 ("Portal de Repositorios Latinoamericanos",
  "Universidad de Chile", "Chile", "Multidisciplinario",
  "https://repositorioslatinoamericanos.uchile.cl/",
  "Buscador creado en 2006 por la Universidad de Chile; reúne más de un "
  "millón de publicaciones de unas noventa instituciones en diecinueve países."),
 ("Latindex — Sistema Regional de Información en Línea",
  "Universidad Nacional Autónoma de México", "México", "Multidisciplinario",
  "https://www.latindex.org/",
  "Catálogo de revistas científicas de Iberoamérica, útil para saber qué "
  "publicaciones existen en cada disciplina y país."),
 ("Biblioteca CLACSO",
  "Consejo Latinoamericano de Ciencias Sociales", "Regional", "Ciencias sociales",
  "https://biblioteca-repositorio.clacso.edu.ar/",
  "Repositorio de ciencias sociales con libros, artículos y documentos de "
  "trabajo de centros de investigación de toda la región."),
 ("DOAJ — Directory of Open Access Journals",
  "DOAJ", "Regional", "Multidisciplinario",
  "https://doaj.org/",
  "Directorio mundial de revistas de acceso abierto revisadas por pares. "
  "Permite filtrar por idioma y por país, y declara la licencia de cada una."),
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
    print(f"  [{cid}] {titulo[:52]:<54} {tema}")

o = io.StringIO()
w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
w.writeheader(); w.writerows(filas)
open("catalogo.csv", "w", encoding="utf-8").write(o.getvalue())
print(f"\n{len(nuevos)} portales añadidos | {len(PORTALES)-len(nuevos)} ya estaban")
