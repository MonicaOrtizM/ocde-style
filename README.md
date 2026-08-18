# ocde-style

Skill para escribir y editar prosa con la arquitectura de párrafo de los
documentos de política de la OCDE. Funciona en español y en inglés.

La idea es simple. Un documento se sigue leyendo cuando cada párrafo es una
unidad corta y autónoma que sostiene su propia afirmación con su propio dato.
Esta skill mide esa arquitectura sobre un corpus real, la enseña y la audita.

> **Si eres un asistente de IA leyendo este repositorio**, el punto de entrada
> es [`SKILL.md`](SKILL.md). Este README es la documentación para personas.

---

## 1. Qué hace y qué no hace

**Hace tres cosas.**

| Modo | Entrada | Salida |
|---|---|---|
| **Generar** | Insumos de cualquier tipo, notas, datos, transcripción, viñetas | Prosa con la arquitectura del perfil |
| **Editar** | Un texto que ya existe | El mismo texto reestructurado por párrafo |
| **Auditar** | Un `.docx`, `.pdf`, `.md` o `.txt` | Qué párrafos partir, qué ideas se repiten, y las frecuencias contra la línea base |

**No hace estas otras.** No verifica que los datos sean ciertos, solo revisa la
forma. No corrige ortografía ni gramática. No traduce. No inventa datos, si una
afirmación no tiene cifra la marca como pendiente de fuente en vez de rellenarla.

---

## 2. De dónde salen las reglas

Todo lo que afirma esta skill sale de medir un corpus. Si el corpus fuera otro,
las reglas serían otras, y por eso conviene saber exactamente cuál se usó.

**El corpus.** Los documentos que la OCDE publica en su sección *Policy papers
and briefs*, filtrados por país e idioma inglés. Se usaron dos filtros de país,
Colombia y México, para comprobar si lo medido era el estilo del emisor o una
particularidad de un país. El enlace de cada documento está en
[`referencias/corpus_ocde.tsv`](referencias/corpus_ocde.tsv), de modo que
cualquiera puede reconstruir el corpus y repetir la medición.

**Los PDF no están en este repositorio.** Son 185 MB de material con derechos de
la OCDE. Aquí están solamente los enlaces, las estadísticas agregadas y los
scripts. Para reconstruirlo se ejecuta `descargar_corpus.py` con el TSV.

**Qué se dejó fuera y por qué.** El corpus se divide en dos. Hay 69 notas de país
de 2 a 20 páginas y 24 publicaciones completas de hasta 669 páginas, porque
algunas entradas del listado enlazan el libro entero en vez del capítulo. Las
publicaciones largas se excluyeron, porque un libro con anexos estadísticos
distorsiona cualquier medida de longitud de párrafo. El perfil sale de las 69
notas cortas, 426 páginas, 1.173 párrafos de prosa y 61.538 palabras.

**Cómo se midió.** `analizar_estilo.py` recorre cada PDF y mide seis rasgos por
párrafo. Número de oraciones, número de palabras, longitud de la primera
oración, si contiene alguna cifra, si contiene un referente de comparación, y si
abre con una fórmula que retrasa la afirmación.

**Dos decisiones técnicas que cambian el resultado.** Los párrafos se toman de
los bloques de maquetación del PDF y no de las líneas en blanco, porque un PDF a
dos columnas no separa párrafos con línea en blanco y dividir por saltos dobles
devuelve un bloque único de veinte oraciones. Y se filtra el aviso de derechos
de autor que se repite en cada nota, porque sin ese filtro el corpus parecía usar
el verbo *must* 85 veces cuando el uso real en prosa es 33.

**Lo que se descartó del texto.** El 82% de los bloques quedó fuera por ser
tablas, leyendas de figuras, encabezados sueltos o texto legal. El perfil
describe la prosa corrida, no el documento completo.

### Lo que arrojó la medición

| Rasgo | Valor |
|---|---|
| Oraciones por párrafo, mediana | 2 |
| Párrafos de una sola oración | 36% |
| Párrafos de una o dos oraciones | 63% |
| Párrafos de cinco o más oraciones | 9% |
| Palabras por párrafo, mediana | 44 (cuartiles 24 y 68) |
| Palabras de la primera oración, mediana | 21 (cuartiles 15 y 27) |
| Primeras oraciones que ya contienen una cifra | 55% |
| Párrafos que abren con *there is* o *it is* | 2% |
| Apariciones de la expresión *OECD average* | 350, una cada 176 palabras |

El perfil descriptivo completo está en
[`referencias/perfil.md`](referencias/perfil.md).

### El perfil no depende del país

Antes de unir los dos filtros se midieron por separado, para comprobar si lo
medido era el estilo del emisor o una particularidad de un país. Colombia aportó
48 notas y México 21.

| Regla | Colombia | México | Diferencia |
|---|---|---|---|
| Párrafo de más de 3 oraciones | 13% | 15% | 2 puntos |
| Párrafo de más de 100 palabras | 7% | 7% | 0 |
| Apertura de más de 35 palabras | 9% | 9% | 0 |
| Apertura que retrasa la afirmación | 1% | 1% | 0 |
| Párrafo sin referente de comparación | 56% | 53% | 3 puntos |
| Párrafo sin ninguna cifra | 29% | 37% | 8 puntos |

**Las cuatro reglas de forma son prácticamente idénticas.** La arquitectura es
del emisor, no del país. La única diferencia apreciable, ocho puntos en párrafos
sin cifra, es de contenido y no de forma.

Por eso el corpus se puede nutrir con notas de cualquier país sin recalibrar.
Ampliar el corpus añade robustez estadística, no cambia las reglas. Comprobado
esto, los dos filtros se unieron en una sola línea base de 69 notas, que es la
que usa el auditor. El detalle está en
[`referencias/validacion-cruzada.md`](referencias/validacion-cruzada.md).

### Dos hipótesis que la medición refutó

Se probaron y no se sostienen. Están aquí porque son intuiciones frecuentes y
conviene no construir reglas sobre ellas.

**La primera oración no es más corta que las demás.** Mediana de 21 palabras
contra 19,3 del resto, y ocurre en el 46% de los párrafos, que es azar.

**No se reserva el dato para el final.** El 55% de las primeras oraciones ya
contiene la cifra. El patrón de abrir sin dato y cuantificar después aparece solo
en el 27% de los párrafos. La fuerza del párrafo no viene de anunciar y luego
demostrar. Viene de que el párrafo es corto, se entiende por separado y sostiene
su afirmación con un dato anclado a un referente.

---

## 3. Las tres reglas que sí se sostienen

**1. El párrafo es una unidad autónoma de una a tres oraciones.** Si no se
entiende por separado, está mal cortado. Si pasa de cuatro oraciones, casi
siempre contiene dos ideas y hay que partirlo.

**2. La afirmación va primero y contiene su dato.** No se anuncia lo que se va a
demostrar. Se afirma con la cifra incluida. La segunda oración amplía, matiza o
compara, nunca repite.

**3. La afirmación se ancla contra un referente.** Un dato solo describe, un dato
contra un punto de comparación afirma. Sirven el promedio de un grupo, la entidad
comparable, el mismo sujeto en otro año, o la meta declarada.

---

## 4. Español e inglés

La skill trabaja en los dos idiomas y reconoce cuál es sin que haya que
indicárselo.

El corpus está en inglés y el español ocupa entre 15% y 20% más palabras para
decir lo mismo, así que los umbrales están ajustados.

| Umbral | Inglés | Español |
|---|---|---|
| Oraciones por párrafo | 3 | 3 |
| Palabras por párrafo | 100 | 100 |
| Palabras de la apertura | 35 | 40 |

**Este ajuste es una conversión razonada, no una medición.** Es la limitación más
importante de la skill y se explica en la sección 9.

---

## 5. Cómo se instala y se usa

### Instalación

Para usarla como skill de Claude Code, se clona dentro de la carpeta de skills.

```bash
git clone https://github.com/MonicaOrtizM/ocde-style ~/.claude/skills/ocde-style
```

También funciona pasándole el enlace del repositorio a un asistente en el chat,
o clonándola en cualquier carpeta y ejecutando los scripts de forma manual.

### Requisitos

Python 3.10 o superior con tres librerías.

```bash
pip install pymupdf python-docx openpyxl
```

En Windows sobre ARM conviene usar el intérprete x64, porque algunas de estas
librerías no publican paquetes precompilados para ARM.

### Modo generar

Se invoca en conversación, no por línea de comandos.

```
/ocde-style genera una nota de dos páginas con estos insumos
```

Se adjunta el material disponible, una hoja de cálculo, unas viñetas, un acta, un
borrador ajeno. El procedimiento que sigue es este.

1. Extrae de los insumos cada afirmación posible con el dato que la sostiene.
2. Descarta los datos que no sostienen ninguna afirmación.
3. Marca como pendiente de fuente las afirmaciones sin dato, no las escribe.
4. Ordena por consecuencia, no por cronología ni por el orden del insumo.
5. Escribe un párrafo por afirmación, nunca dos afirmaciones en uno.
6. Audita el resultado y corrige lo que se aparte del perfil.

### Modo editar

```
/ocde-style edita este documento
```

Primero audita, después interviene solo donde el número lo pide. Un párrafo de
cinco oraciones se parte por la segunda idea. Un párrafo sin dato se devuelve
con la pregunta de qué lo sostiene. Un párrafo sin referente se ancla.

**Nunca suprime datos ciertos.** Si una afirmación no se puede verificar, la
conserva y pregunta.

### Modo auditar

Es el único que se ejecuta directamente, y no modifica el archivo.

```bash
python scripts/auditar_texto.py --texto borrador.docx
```

Acepta `.docx`, `.pdf`, `.md` y `.txt`. Reconoce el idioma por sí mismo. Para
indicarlo de forma explícita o para guardar el informe

```bash
python scripts/auditar_texto.py --texto nota.pdf --idioma en --salida informe.md
```

---

## 6. Cómo se lee la salida del auditor

```
  Regla                                         texto   OCDE
----------------------------------------------------------------------
  Párrafo de más de 3 oraciones                   78%    13%  <<
  Párrafo de más de 100 palabras                  56%     6%  <<
  Apertura de más de 40 palabras                   0%     8%
  Párrafo sin ninguna cifra                       44%    33%
  Párrafo sin referente de comparación            56%    58%
  Apertura que retrasa la afirmación               0%     1%
======================================================================
  Señalados por estructura     8 de 9
  Párrafos 7, 12, 13, 17, 6, 16, 20, 9
  Pares que se repiten         0   (solapamiento >= 0.75)
```

**La columna de la derecha no es un objetivo de cero.** Es la frecuencia con que
la propia OCDE se aparta de cada regla, medida con estas mismas reglas sobre las
69 notas. El 13% de los párrafos de la OCDE pasa de tres oraciones, y eso está
bien.

Lo que importa es la distancia. Las dos flechas señalan que ese texto tiene seis
veces más párrafos largos y ocho veces más párrafos pesados que el corpus. Las
otras cuatro filas están en línea, así que ahí no hay nada que corregir. Un `<<`
aparece cuando la tasa del texto está veinte puntos o más por encima de la
referencia.

**Las dos últimas líneas son las accionables.** La primera dice qué párrafos hay
que partir, ordenados del más pesado al menos. La segunda dice qué ideas se
repiten, y se explica en la sección siguiente.

**Por qué no hay un porcentaje de cumplimiento.** La primera versión daba un
veredicto de cumple o no cumple exigiendo las seis reglas a la vez, y al probarla
contra las propias notas de la OCDE arrojó entre 6% y 45% de cumplimiento. Una
medida que reprueba al corpus del que salió está mal. Por eso ahora cada regla se
reporta por separado y contra su línea base. Si adaptas esta skill, conserva esa
prueba de control.

---

## 7. Ideas que se repiten

El auditor compara todos los párrafos contra todos, no solo los contiguos,
porque la repetición que más estorba suele estar a varias páginas de distancia.
La comparación es de vocabulario, sobre las raíces de las palabras con carga
semántica y las cifras que cada párrafo cita.

Para cada par señalado devuelve una de tres acciones, y la distinción importa.

| Solapamiento | ¿Caben juntos? | Acción |
|---|---|---|
| 0,90 o más | indiferente | **Eliminar uno.** Afirman lo mismo, no hay nada que combinar |
| Entre 0,75 y 0,90 | sí | **Fusionar.** Misma idea con aportes distintos |
| Entre 0,75 y 0,90 | no | **Depurar.** Revisar si es repetición o son dos ideas |

**La tercera fila es la que evita que esta función pelee con el perfil.**
Fusionar dos párrafos hasta pasar de tres oraciones cambia un defecto por otro.

Así se ve sobre un texto con repetición deliberada.

```
**Párrafos 3 y 4**, solapamiento 0.9, contiguos.
  Comparten. presid, miembr, ordina, fusion, asesor, reunio, direct, minist
  **Eliminar uno.** Con este solapamiento los dos afirman lo mismo y no hay nada
  que combinar. Conservar el que traiga el dato más preciso o la fuente más
  fuerte, y borrar el otro.

**Párrafos 1 y 2**, solapamiento 0.75, contiguos.
  Comparten. minist, agenci, presup. Misma cifra, 95
  **Fusionar.** Tratan la misma idea con aportes distintos. Juntos dan 2
  oraciones y 23 palabras, así que caben en un párrafo. La afirmación común va en
  la primera oración y los dos datos en la segunda.
```

**El corpus de la OCDE no sirve de referencia para esta regla.** Sus notas de
país siguen plantilla y repiten por diseño. Una sola nota de TALIS arrojó 201
pares, casi todos leyendas de figuras con la misma estructura. Por eso el umbral
no se fijó imitando al corpus, sino por su distribución de similitudes, cuyo
percentil 99 está en 0,86. El valor por defecto es 0,75 y se cambia con
`--umbral-redundancia`.

**Detecta vocabulario, no significado.** Dos párrafos que dicen lo mismo con
palabras distintas no se detectan. En español la comparación usa las raíces
truncadas de las palabras, porque sin eso *designados* y *designa* cuentan como
términos diferentes y dos párrafos casi idénticos quedan por debajo del umbral.

---

## 8. Cuándo usarla y cuándo no

**Sirve bien para esto.**

- Convertir insumos dispersos en una nota corta que se lea sin detenerse.
- Aligerar un borrador propio que quedó con párrafos de seis oraciones.
- Notas técnicas, fichas de proyecto, resúmenes ejecutivos, one pagers.
- Auditar un documento antes de devolver comentarios, para separar lo que es
  problema de forma de lo que es problema de fondo.
- Columnas y textos de opinión, con la advertencia de que ahí la regla del dato
  en cada párrafo puede sobrar.

**No sirve para esto.**

- Textos normativos, contratos y términos de referencia, donde la oración larga
  con subordinadas es funcional y partirla cambia el sentido.
- Documentos académicos con argumentación extendida, donde un párrafo tiene que
  desarrollar un razonamiento completo.
- Prosa literaria o narrativa personal.
- Idiomas distintos del español y el inglés.

**Zona intermedia.** En un documento largo conviene aplicarla al resumen
ejecutivo y a las secciones de hallazgos, y no aplicarla a los anexos
metodológicos.

---

## 9. Limitaciones

**Los umbrales del español no están medidos.** Salen de aplicar un factor de
expansión razonable sobre una medición hecha en inglés. Para fijarlos con datos
habría que reunir un corpus comparable de documentos de política en español y
ejecutar los scripts sobre él. Mientras tanto, la línea base que se usa para
comparar un texto en español es la inglesa, y el auditor lo advierte cada vez.

**El perfil viene de un solo género y un solo emisor.** Son notas de país de la
OCDE, documentos descriptivos que posicionan a un país contra un promedio. Un
policy paper con recomendaciones o un documento de proyecto tienen otras
necesidades, y aplicar este perfil sin criterio los puede volver telegráficos.

**El corpus está filtrado por dos países de América Latina.** No se probó contra
notas de países europeos o asiáticos, ni contra otros géneros de la OCDE, ni
contra documentos escritos originalmente en español.

**La detección de referente es imprecisa.** Funciona con una lista de
expresiones, y por eso el 58% del propio corpus aparece marcado como sin
referente. Esa tasa mide tanto el texto como los límites de la lista. Sirve como
señal, no como veredicto.

**La extracción de PDF pierde contenido.** Se descarta el 82% de los bloques y
algo de prosa se pierde junto con las tablas. En `.docx` la lectura es más
limpia, aunque el texto dentro de tablas y cuadros no se audita.

**La forma no corrige el fondo.** Un párrafo corto con un dato falso sigue siendo
falso. La verificación del dato contra su fuente es otra tarea.

---

## 10. Recalibrar contra otro corpus

El perfil no es definitivo. Para calibrar contra otra institución, por ejemplo la
CEPAL, el Banco Mundial o un ministerio, se descargan sus documentos y se
ejecutan dos comandos.

```bash
python scripts/analizar_estilo.py --corpus "ruta al corpus" --salida perfil.md --max-paginas 20
```

```bash
python scripts/auditar_texto.py --calcular-base "ruta al corpus" --idioma es
```

El primero produce el perfil descriptivo. El segundo produce la línea base que el
auditor usa para comparar, y la guarda en `referencias/base_es.json`.

Para descargar un corpus desde una lista de enlaces

```bash
python scripts/descargar_corpus.py --lista pdfs.tsv --destino "carpeta"
```

**Nota sobre el sitio de la OCDE.** Sus páginas HTML están detrás de Cloudflare y
responden 403 a un cliente de Python, pero los PDF bajo `/content/dam/` se sirven
sin bloqueo. Por eso los enlaces se resuelven desde un navegador y la descarga se
hace aparte. Si algún día el dominio de contenido también se protege, el error no
está en el script.

---

## 11. Archivos

```
ocde-style/
├── SKILL.md                        Punto de entrada para el asistente
├── README.md                       Este archivo
├── referencias/
│   ├── perfil.md                   Perfil descriptivo del corpus
│   ├── base_en.json                Línea base por regla, inglés
│   ├── validacion-cruzada.md       Comparación entre los dos países
│   └── corpus_ocde.tsv             Los 93 enlaces del corpus
└── scripts/
    ├── auditar_texto.py            Mide un texto y calcula líneas base
    ├── analizar_estilo.py          Recalibra el perfil desde un corpus
    └── descargar_corpus.py         Descarga un corpus desde una lista
```

---

## Créditos y alcance

Este trabajo no está afiliado a la OCDE ni cuenta con su respaldo. Es un análisis
independiente de estilo hecho sobre documentos que la organización publica de
forma abierta.

El repositorio no redistribuye esos documentos. Contiene los enlaces públicos,
estadísticas agregadas derivadas del análisis y los scripts que producen ambas
cosas. Los derechos de las publicaciones son de la OCDE y se consultan en su
sitio.

El código se publica bajo licencia MIT.
