# Validación cruzada entre países

El perfil se construyó con el filtro de un solo país, Colombia. Quedaba abierto
si la arquitectura de párrafo dependía de ese filtro o era del emisor. Se probó
repitiendo la medición completa sobre un segundo filtro, México.

## Los dos corpus

| | Colombia | México |
|---|---|---|
| Notas de país | 48 | 21 |
| Párrafos de prosa | 1.195 | 529 |

Ambos en inglés, ambos medidos con las mismas seis reglas y el mismo script,
`auditar_texto.py --calcular-base`.

## Resultado

| Regla | Colombia | México | Diferencia |
|---|---|---|---|
| Párrafo de más de 3 oraciones | 13% | 15% | 2 puntos |
| Párrafo de más de 100 palabras | 7% | 7% | 0 |
| Apertura de más de 35 palabras | 9% | 9% | 0 |
| Apertura que retrasa la afirmación | 1% | 1% | 0 |
| Párrafo sin referente de comparación | 56% | 53% | 3 puntos |
| Párrafo sin ninguna cifra | 29% | 37% | 8 puntos |

**Las cuatro reglas de forma son prácticamente idénticas.** Longitud de párrafo,
longitud de apertura y tipo de apertura no se mueven más de dos puntos entre un
corpus y otro. La arquitectura es del emisor, no del país.

**La única diferencia apreciable es de contenido, no de forma.** México tiene
ocho puntos más de párrafos sin ninguna cifra, lo que refleja qué se dice en cada
nota y no cómo se construye el párrafo.

## Qué implica

El perfil se puede nutrir con notas de cualquier país sin recalibrar. Ampliar el
corpus añade robustez estadística, no cambia las reglas.

## Qué sigue abierto

Los dos corpus son de países de América Latina. No se probó contra notas de
países europeos o asiáticos, ni contra otros géneros de la OCDE, ni contra
documentos en español.

La línea base que usa el auditor sigue siendo la de Colombia, en
`base_en.json`, porque es la más grande de las dos. Para reemplazarla por una
combinada se juntan los PDF en una carpeta y se corre

```bash
python scripts/auditar_texto.py --calcular-base "carpeta" --idioma en
```
