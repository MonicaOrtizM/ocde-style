# Validación cruzada entre países

El perfil se construyó con el filtro de un país, Colombia. Quedaba abierto si la
arquitectura de párrafo dependía de ese filtro o era del emisor. Se probó
repitiendo la medición completa sobre un segundo filtro, México.

## Los dos corpus

| | Colombia | México |
|---|---|---|
| Notas de país | 48 | 21 |
| Párrafos de prosa | 801 | 377 |

Ambos en inglés, ambos medidos con las mismas seis reglas, el mismo criterio de
prosa y el mismo script, `auditar_texto.py --calcular-base`.

## Resultado

| Regla | Colombia | México | Diferencia |
|---|---|---|---|
| Párrafo de más de 3 oraciones | 19% | 20% | 1 punto |
| Párrafo de más de 100 palabras | 10% | 9% | 1 punto |
| Apertura de más de 35 palabras | 11% | 10% | 1 punto |
| Apertura que retrasa la afirmación | 2% | 2% | 0 |
| Párrafo sin referente de comparación | 44% | 45% | 1 punto |
| Párrafo sin ninguna cifra | 24% | 34% | 10 puntos |

**Cinco de las seis reglas quedan dentro de un punto.** Longitud de párrafo,
longitud de apertura, tipo de apertura y presencia de referente no se mueven de
un corpus a otro. La arquitectura es del emisor, no del país.

**La única diferencia apreciable es de contenido, no de forma.** México tiene
diez puntos más de párrafos sin ninguna cifra, lo que refleja qué se dice en cada
nota y no cómo se construye el párrafo.

## Qué se hizo con el resultado

Comprobada la equivalencia, los dos filtros se unieron en un solo corpus de 69
notas, 426 páginas, 1.178 párrafos de prosa y 61.640 palabras. Esa es la línea
base que usa el auditor, en `base_en.json`, y de ahí salen los números del
`README.md` y del `SKILL.md`.

| Regla | Línea base combinada |
|---|---|
| Párrafo de más de 3 oraciones | 19% |
| Párrafo de más de 100 palabras | 10% |
| Apertura de más de 35 palabras | 11% |
| Párrafo sin ninguna cifra | 27% |
| Párrafo sin referente de comparación | 44% |
| Apertura que retrasa la afirmación | 2% |

## Nota sobre estas cifras

Son distintas de las que tuvo una versión anterior de este archivo. La causa no
fue el corpus sino el criterio de prosa. El analizador y el auditor filtraban los
bloques con reglas distintas, así que medían poblaciones distintas del mismo
material, y el mismo corpus daba 36% de párrafos de una sola oración en un
archivo y 55% en el otro. Desde que las dos herramientas comparten `prosa.py`
las dos ven los mismos 1.178 párrafos.

## Qué sigue abierto

Los dos filtros son de países de América Latina. No se probó contra notas de
países europeos o asiáticos, ni contra otros géneros de la OCDE, ni contra
documentos escritos originalmente en español.

Para añadir un tercer país se descargan sus notas a la misma carpeta y se ejecuta

```bash
python scripts/auditar_texto.py --calcular-base "carpeta" --idioma en
```
