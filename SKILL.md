---
name: ocde-style
description: Convierte insumos cualquiera (notas, datos, transcripciones, borradores) en prosa con la arquitectura de párrafo de los documentos de política de la OCDE. Cada párrafo es una unidad autónoma de una a tres oraciones que carga su propio dato anclado a un referente. Funciona en español y en inglés. Tres modos, generar, editar y auditar. Trigger — /ocde-style, "escríbelo estilo OCDE", "vuelve esto párrafos que enganchen", "audita este texto contra el perfil".
---

# Estilo OCDE

Esta skill no imita el tema ni el género de la OCDE. Imita la arquitectura del
párrafo, que es lo que hace que un documento se siga leyendo. El perfil está
medido sobre 69 notas de país, 1.173 párrafos y 61.538 palabras, con dos filtros
de país distintos. La construcción completa, los casos de uso y las limitaciones
están en `README.md`, que debe leerse antes de la primera aplicación.

## Las tres reglas

**1. El párrafo es una unidad autónoma de una a tres oraciones.** Mediana medida
de 2 oraciones y 44 palabras. El 36% de los párrafos del corpus tiene una sola
oración y solo el 9% pasa de cinco. Si un párrafo no se puede leer suelto está
mal cortado, y si pasa de cuatro oraciones casi siempre tiene dos ideas adentro.

**2. La afirmación va primero y trae su dato adentro.** El 55% de las primeras
oraciones del corpus ya contiene una cifra. No se anuncia lo que se va a
demostrar, se afirma con el número puesto. La segunda oración amplía, matiza o
compara, nunca repite.

**3. La afirmación se ancla contra un referente.** La sola expresión *OECD
average* aparece 350 veces, una cada 176 palabras. Sirven el promedio de un
grupo, la entidad comparable, el mismo sujeto en otro año, o la meta declarada.

## Lo que el corpus refuta

No construir reglas sobre esto, porque los datos dicen que no existe.

- **La primera oración no es más corta.** 21 palabras contra 19,3 del resto, en
  el 46% de los párrafos, que es azar.
- **No se reserva el dato para el final.** El patrón de abrir sin cifra y
  cuantificar después aparece solo en el 27% de los párrafos.

## El perfil no depende del país

El corpus se armó con dos filtros de país, Colombia y México, medidos por
separado antes de unirlos. Las cuatro reglas de forma no se movieron más de dos
puntos entre uno y otro, así que la arquitectura es del emisor y no del país. La
única diferencia apreciable fue de contenido, ocho puntos en párrafos sin cifra.

Consecuencia práctica. El corpus se puede nutrir con notas de cualquier país sin
recalibrar. Ampliar el corpus añade robustez estadística, no cambia las reglas.
El detalle está en `referencias/validacion-cruzada.md`.

## Umbrales

| Umbral | Inglés | Español |
|---|---|---|
| Oraciones por párrafo | 3 | 3 |
| Palabras por párrafo | 100 | 100 |
| Palabras de la apertura | 35 | 40 |

Los del español son una conversión razonada sobre una medición hecha en inglés,
no una medición propia. Decirlo cuando se reporte un resultado en español.

## Estilo de casa

Si quien usa la skill tiene reglas propias de redacción, van en un archivo
`estilo-de-casa.md` junto a este y se aplican **después** de las tres reglas de
arriba. Ejemplos de reglas de casa son la prohibición de ciertos signos, el
tratamiento de las enumeraciones, o el formato de las citas. La skill no trae
ninguna por defecto.

## Los tres modos

### Generar
1. Extraer de los insumos cada afirmación posible con el dato que la sostiene.
2. Descartar los datos que no sostienen ninguna afirmación.
3. Marcar como pendiente de fuente las afirmaciones sin dato. **No rellenarlas.**
4. Ordenar por consecuencia, no por cronología ni por el orden del insumo.
5. Un párrafo por afirmación. Nunca dos afirmaciones en un párrafo.
6. Auditar el resultado y corregir lo que se aparte de la línea base.

### Editar
Auditar primero, intervenir solo donde el número lo pide.

- Párrafo de cuatro o más oraciones. Buscar la segunda idea y partirlo.
- Párrafo sin cifra. Preguntar qué dato lo sostiene. Si no hay, es opinión y
  debe decirse como tal.
- Párrafo sin referente. Añadir contra qué se compara.
- Apertura con hay, es importante, este documento, cabe señalar, según.
  Reescribir poniendo el sujeto real al frente.
- **No suprimir datos ciertos.** Si algo no se puede verificar, se deja y se
  pregunta. El silencio también es una afirmación.

### Auditar
```bash
python scripts/auditar_texto.py --texto borrador.docx
```
Acepta `.docx`, `.pdf`, `.md`, `.txt`. Detecta el idioma solo.

**Cómo se lee.** El informe da la frecuencia de cada regla en el texto contra la
frecuencia en el corpus de la OCDE. La referencia no es cero. El 14% de los
párrafos de la OCDE pasa de tres oraciones. Lo que importa es la distancia, y
solo se señala lo que está veinte puntos o más por encima.

**No inventar un porcentaje de cumplimiento.** La primera versión exigía las seis
reglas a la vez y reprobaba a las propias notas de la OCDE con 6% a 45% de
cumplimiento. Por eso cada regla se reporta por separado.

## Scripts

| Script | Para qué |
|---|---|
| `scripts/auditar_texto.py` | Audita un texto, y con `--calcular-base` mide un corpus |
| `scripts/analizar_estilo.py` | Recalibra el perfil descriptivo desde un corpus de PDF |
| `scripts/descargar_corpus.py` | Baja un corpus desde una lista de enlaces |

## Límites que hay que declarar al entregar

- Los umbrales del español no están medidos, son una conversión razonada.
- El perfil viene de un solo género y un solo emisor, notas de país descriptivas.
- Los dos filtros de país son de América Latina. No se probó contra notas de
  países europeos o asiáticos.
- La detección de referente usa una lista de expresiones y marca como sin
  referente al 55% del propio corpus. Es señal, no veredicto.
- Se descarta el 82% de los bloques del PDF por ser tablas y leyendas.
- Un párrafo corto con un dato falso sigue siendo falso. La verificación del
  dato es otra tarea.

## Cuándo no aplicarla

Términos de referencia y textos normativos, donde la oración larga con
subordinadas es funcional. Documentos académicos con argumentación extendida.
Prosa personal como un diario. En documentos largos, aplicarla al resumen
ejecutivo y a los hallazgos, y dejar los anexos metodológicos en paz.
