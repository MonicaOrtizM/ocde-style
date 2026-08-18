---
name: ocde-style
description: Convierte insumos de cualquier tipo (notas, datos, transcripciones, borradores) en prosa con la arquitectura de párrafo de los documentos de política de la OCDE. Cada párrafo es una unidad autónoma de una a tres oraciones que carga su propio dato anclado a un referente. Funciona en español y en inglés. Tres modos, generar, editar y auditar. Trigger — /ocde-style, "escríbelo estilo OCDE", "vuelve esto párrafos que enganchen", "audita este texto contra el perfil".
---

# Estilo OCDE

Esta skill no imita el tema ni el género de la OCDE. Imita la arquitectura del
párrafo, que es lo que hace que un documento se siga leyendo. El perfil está
medido sobre 69 notas de país, 1.178 párrafos y 61.640 palabras, con dos filtros
de país distintos. La construcción completa, los casos de uso y las limitaciones
están en `README.md`, que debe leerse antes de la primera aplicación.

## Las tres reglas

**1. El párrafo es una unidad autónoma de una a tres oraciones.** Mediana medida
de 2 oraciones y 43 palabras. El 36% de los párrafos del corpus tiene una sola
oración y solo el 9% pasa de cinco. Si un párrafo no se entiende por separado
está mal cortado, y si pasa de cuatro oraciones casi siempre contiene dos ideas.

**2. La afirmación va primero y contiene su dato.** El 54% de las primeras
oraciones del corpus ya contiene una cifra. No se anuncia lo que se va a
demostrar, se afirma con la cifra incluida. La segunda oración amplía, matiza o
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
separado antes de unirlos. Cinco de las seis reglas no se movieron más de un
punto entre uno y otro, así que la arquitectura es del emisor y no del país. La
única diferencia apreciable fue de contenido, diez puntos en párrafos sin cifra.

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

**Se pueden subir, pero tienen techo.** Con `--max-oraciones`, `--max-palabras` y
`--max-apertura` el usuario ajusta cada umbral. Por encima del techo el auditor
se niega y explica por qué.

| Umbral | Por defecto | Techo | Por qué ese techo |
|---|---|---|---|
| Oraciones por párrafo | 3 | **5** | Con más de cinco el párrafo deja de entenderse por separado y la regla 1 pierde sentido. En el corpus solo el 9% llega a ese tamaño |
| Palabras por párrafo | 100 | **150** | El p90 del corpus es 98. Por encima de 150 ya no se mide este estilo |
| Palabras de la apertura | 35 en, 40 es | **60** | El p90 de la apertura es 35. Una de más de 60 no afirma, enumera |

Cuando se ajusta un umbral el informe lo dice en la cabecera, para que nadie lea
un resultado creyendo que salió del perfil por defecto.

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
- Par de párrafos que se repiten. Aplicar la acción que indique el informe,
  eliminar uno, fusionar o depurar. No fusionar por costumbre.
- Apertura con hay, es importante, este documento, cabe señalar, según.
  Reescribir poniendo el sujeto real al frente.
- **No suprimir datos ciertos.** Si algo no se puede verificar, se deja y se
  pregunta. El silencio también es una afirmación.

### Auditar
```bash
python scripts/auditar_texto.py --texto borrador.docx
```
Acepta `.docx`, `.pdf`, `.md`, `.txt`. Reconoce el idioma por sí mismo.

**Cómo se lee.** El informe da la frecuencia de cada regla en el texto contra la
frecuencia en el corpus de la OCDE. La referencia no es cero. El 19% de los
párrafos de la OCDE pasa de tres oraciones. Lo que importa es la distancia, y
solo se señala lo que está veinte puntos o más por encima.

El informe cierra con dos listas accionables. Los párrafos que hay que partir,
porque pasan de tres oraciones o de cien palabras. Y los pares de párrafos que
dicen lo mismo, explicados abajo.

## Ideas que se repiten

El auditor compara todos los párrafos contra todos, no solo los contiguos,
porque la repetición que más estorba suele estar a varias páginas de distancia.
Para cada par señalado devuelve una de tres acciones, y hay que respetar cuál.

**Solapamiento de 0,90 o más. Eliminar uno.** Los dos afirman lo mismo y no hay
nada que combinar. Se conserva el que traiga el dato más preciso o la fuente más
fuerte.

**Entre 0,75 y 0,90, y juntos caben en un párrafo. Fusionar.** Tratan la misma
idea con aportes distintos. La afirmación común va en la primera oración y los
dos datos en la segunda.

**Entre 0,75 y 0,90, y juntos no caben. Depurar, no fusionar.** Hay que revisar
si es una idea repetida o dos ideas que comparten vocabulario. Si es lo primero,
se deja una sola afirmación con el mejor dato.

**La tercera regla es la que evita que esta función pelee con el perfil.**
Fusionar dos párrafos hasta pasar de tres oraciones cambia un defecto por otro.

**El corpus de la OCDE no sirve de referencia para esta regla.** Sus notas de
país siguen plantilla y repiten por diseño, hasta 201 pares en una sola nota. El
umbral de 0,75 sale de la distribución de similitudes del corpus, cuyo percentil
99 está en 0,86, y no de imitar su tasa de repetición. Se ajusta con
`--umbral-redundancia`.

**No inventar un porcentaje de cumplimiento.** La primera versión exigía las seis
reglas a la vez y reprobaba a las propias notas de la OCDE con 6% a 45% de
cumplimiento. Por eso cada regla se reporta por separado.

## Scripts

| Script | Para qué |
|---|---|
| `scripts/auditar_texto.py` | Audita un texto, y con `--calcular-base` mide un corpus |
| `scripts/analizar_estilo.py` | Recalibra el perfil descriptivo desde un corpus de PDF |
| `scripts/descargar_corpus.py` | Descarga un corpus desde una lista de enlaces |
| `scripts/prosa.py` | Criterio único de qué bloque cuenta como prosa. Lo usan los otros dos |

## Límites que hay que declarar al entregar

- Los umbrales del español no están medidos, son una conversión razonada.
- El perfil viene de un solo género y un solo emisor, notas de país descriptivas.
- Los dos filtros de país son de América Latina. No se probó contra notas de
  países europeos o asiáticos.
- La detección de referente es imprecisa, usa una lista de expresiones y marca
  como sin referente al 44% del propio corpus. Es señal, no veredicto.
- La detección de repetición compara vocabulario, no significado. Dos párrafos
  que hablan del mismo tema con palabras distintas no se detectan.
- Se descarta el 82% de los bloques del PDF por ser tablas y leyendas.
- Un párrafo corto con un dato falso sigue siendo falso. La verificación del
  dato es otra tarea.

## Cuándo no aplicarla

Términos de referencia y textos normativos, donde la oración larga con
subordinadas es funcional. Documentos académicos con argumentación extendida.
Prosa personal como un diario. En documentos largos, aplicarla al resumen
ejecutivo y a los hallazgos, y no aplicarla a los anexos metodológicos.
