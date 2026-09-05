#!/usr/bin/env python3
"""Genera las obras científicas halladas en Wikisource.

Solo se toman las que Wikisource declara corregidas o validadas —cotejadas
contra el facsímil por una o dos personas—, que es el criterio con que se
descartó Memoria Chilena como fuente directa.
"""
import json, pathlib

CAT = "un catálogo de literatura latinoamericana y española en dominio público"
OBRAS = [
 ("Historia general de la medicina en Chile", "hm-medicinachile",
  "Historia General de la Medicina en Chile", "Pedro Lautaro Ferrer",
  "Chile", 1904, "Medicina",
  "Tomo I, desde 1535 hasta la inauguración de la Universidad de Chile en 1843. "
  "Impreso en Talca por J. Martín Garrido. La Biblioteca Nacional de Chile lo "
  "declara patrimonio cultural común."),
 ("Modo de hacer la operación cesárea", "rb-cesarea",
  "Modo de Hacer la Operación Cesárea", "Josef Ribes y Manuel Bonafós",
  "España", 1805, "Medicina",
  "Instrucción publicada en 1805; sus autores figuran en la propia edición."),
 ("Origen y descubrimiento de la vacuna", "fc3-vacuna",
  "Origen y Descubrimiento de la Vacuna", "François Chaussier",
  "Francia", 1804, "Medicina",
  "Traducción al castellano de Pedro Hernández, publicada en 1804, pocos años "
  "después de que Jenner diera a conocer la vacunación."),
 ("El tamaño del espacio", "lu2-tamanoespacio",
  "El Tamaño del Espacio", "Leopoldo Lugones",
  "Argentina", 1921, "Física",
  "Ensayo de divulgación sobre la teoría de la relatividad, escrito seis años "
  "después de que Einstein publicara la relatividad general."),
]
cid = 976
for pagina, archivo, titulo, autor, pais, anio, tema, nota in OBRAS:
    c = {"slug": archivo.split("-",1)[1], "titulo": titulo, "autor": autor,
         "anio": anio, "tipo": "prosa", "wikisource": pagina, "catalogo": CAT,
         "fuente": {"nota": nota}, "catalogo_id": cid,
         "catalogo_campos": {"dominio":"Ciencia","titulo":titulo,"autor":autor,
            "anio":str(anio),"pais":pais,"genero":tema,"tema":tema,
            "tipo":"Dominio público","puede_alojarse":"si"},
         "opciones":{"salto_por_capitulo":True,"hyphenation":"es"}}
    pathlib.Path(f"obras/{archivo}.json").write_text(
        json.dumps(c, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"  {archivo+'.json':<24} {titulo[:38]:<40} {tema:<12} {pais}")
    cid += 1
print(f"\n{len(OBRAS)} configuraciones, ids 976-{cid-1}")
