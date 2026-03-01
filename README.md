# emovi-mcp

[![CI](https://github.com/Lalitronico/emovi-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Lalitronico/emovi-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/emovi-mcp)](https://pypi.org/project/emovi-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/emovi-mcp)](https://pypi.org/project/emovi-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Servidor MCP para la encuesta ESRU-EMOVI 2023 de movilidad social en México.

*MCP server for the ESRU-EMOVI 2023 social mobility survey (Mexico).*

---

## ¿Qué es esto?

**emovi-mcp** permite que asistentes de IA (Claude, ChatGPT, etc.) consulten la encuesta de movilidad social más completa de México mediante lenguaje natural. Expone cómputos estadísticos ponderados, matrices de transición intergeneracional y exploración de variables como herramientas MCP.

## Sobre la ESRU-EMOVI 2023

La encuesta ESRU-EMOVI 2023, levantada por el Centro de Estudios Espinosa Yglesias (CEEY), es representativa a nivel nacional sobre movilidad social en México. Cubre 17,843 entrevistados de 25 a 64 años, con factores de expansión que representan ~60 millones de personas.

**Bases de datos incluidas:**
| Base de datos | Descripción | Registros | Variables |
|---------------|-------------|-----------|-----------|
| `entrevistado` | Datos del entrevistado principal | 17,843 | ~296 |
| `hogar` | Roster del hogar | 55,477 | ~56 |
| `ingreso_2017` | Ingreso imputado 2017 (comparación temporal) | 17,665 | ~2 |
| `inclusion_financiera` | Módulo de inclusión financiera | 5,976 | ~109 |

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/Lalitronico/emovi-mcp.git
cd emovi-mcp

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar en modo editable con dependencias de desarrollo
pip install -e ".[dev]"

# Opcional: soporte de visualización
pip install -e ".[dev,viz]"
```

O instalar directamente desde PyPI:

```bash
pip install emovi-mcp
# Con soporte de visualización
pip install emovi-mcp[viz]
```

### Prerrequisitos

- Python >= 3.10
- Archivos .dta de la ESRU-EMOVI 2023 (obtener del [CEEY](https://ceey.org.mx/emovi/))

## Configuración

Establecer la variable de entorno `EMOVI_DATA_DIR` apuntando al directorio con los archivos .dta:

```bash
# Linux/Mac
export EMOVI_DATA_DIR="/ruta/a/Esru Emovi 2023/_extracted/3 BASES DE DATOS/Data"

# Windows (PowerShell)
$env:EMOVI_DATA_DIR = "C:\ruta\a\Esru Emovi 2023\_extracted\3 BASES DE DATOS\Data"

# Windows (cmd)
set EMOVI_DATA_DIR=C:\ruta\a\Esru Emovi 2023\_extracted\3 BASES DE DATOS\Data
```

## Uso con Claude Desktop

Agregar lo siguiente al archivo `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "emovi-mcp": {
      "command": "C:/ruta/a/emovi-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "emovi_mcp"],
      "env": {
        "EMOVI_DATA_DIR": "C:/ruta/a/3 BASES DE DATOS/Data"
      }
    }
  }
}
```

En macOS/Linux, reemplazar `Scripts/python.exe` por `bin/python`.

## Herramientas

El servidor expone 11 herramientas MCP:

| Herramienta | Descripción |
|-------------|-------------|
| `describe_survey` | Panorama de la encuesta: bases de datos, tamaño muestral, diseño, dimensiones |
| `list_variables` | Explorar variables por base, sección o palabra clave |
| `variable_detail` | Información completa de una variable: etiqueta, valores, sección, base |
| `tabulate` | Tabulación cruzada ponderada (fila x columna con factores de expansión) |
| `transition_matrix` | Matriz de movilidad intergeneracional con índices formales (Shorrocks, Prais, razón de momios) y errores estándar opcionales vía linealización de Taylor |
| `weighted_stats` | Estadísticas descriptivas: media, mediana, desviación estándar, cuantiles (ponderados) |
| `compare_groups` | Comparar una variable entre grupos (media, mediana o distribución) |
| `filter_data` | Extraer registros con filtros opcionales (máximo 100 filas) |
| `financial_inclusion_summary` | Análisis de inclusión financiera: ahorro, crédito, banca, alfabetización, discriminación |
| `income_comparison` | Comparación temporal de ingreso 2017 vs 2023 con clasificación por línea de pobreza |
| `visualize_mobility` | Generar heatmaps, diagramas Sankey o gráficas de barras para matrices de movilidad (requiere `[viz]`) |

### Ejemplos de consultas

Una vez conectado, puedes preguntar al asistente de IA cosas como:

- *"¿Cuál es la distribución educativa por sexo?"*
  → Usa `tabulate(row_var="educ", col_var="sexo")`

- *"Muéstrame la matriz de movilidad educativa intergeneracional"*
  → Usa `transition_matrix(dimension="education")`

- *"¿Cuál es el ingreso promedio por región?"*
  → Usa `weighted_stats(variable="ingc_pc", by="region_14")`

- *"Compara la movilidad educativa entre hombres y mujeres"*
  → Usa `transition_matrix(dimension="education", by="sexo")`

- *"¿Qué variables hay sobre educación?"*
  → Usa `list_variables(search="educ")`

## Diccionario de variables

El proyecto incluye un diccionario preconstruido con 792 variables extraídas de la documentación oficial del CEEY y los metadatos de los archivos .dta. Soporta búsqueda por nombre, descripción, base de datos y sección.

Para reconstruir el diccionario desde los datos fuente:

```bash
python scripts/build_dictionary.py
```

Esto requiere el archivo `Diccionario ESRU EMOVI 2023.xlsx` en el directorio de datos.

## Ejecutar pruebas

```bash
pytest
```

Las 96 pruebas cubren estadísticas ponderadas, matrices de transición, índices de movilidad, errores estándar por linealización de Taylor, inclusión financiera, comparación temporal de ingreso, visualización y funcionalidad del diccionario de variables, todo con datos sintéticos (no se requieren microdatos reales).

## Notas técnicas

- **Todas las estadísticas son ponderadas** usando la variable de expansión `factor` (o `fac_inc` para el módulo de inclusión financiera)
- **pyreadstat carga los .dta con `apply_value_formats=False`** para evitar crashes por etiquetas duplicadas de municipios
- **`padres_edu`** se construye como `max(educp, educm)` siguiendo la metodología del .do del CEEY
- **Índice de riqueza** usa PCA sobre indicadores binarios de activos del hogar (Filmer & Pritchett, 2001), como alternativa al enfoque MCA del CEEY
- **Errores estándar** usan linealización de Taylor para estimadores de razón bajo muestreo estratificado por conglomerados (UPM/estrato)
- **Índices de movilidad**: Shorrocks M, probabilidad de escape de Prais, correlación intergeneracional de Pearson r, razón de momios de esquina
- **Transporte STDIO**: El servidor se comunica por entrada/salida estándar, compatible con Claude Desktop y otros clientes MCP

## Estructura del proyecto

```
emovi-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .github/workflows/
│   ├── ci.yml                    # CI: pytest en Python 3.10/3.11/3.12
│   └── publish.yml               # Publicar en PyPI al crear release
├── scripts/
│   └── build_dictionary.py       # Constructor del diccionario
├── src/emovi_mcp/
│   ├── __init__.py
│   ├── __main__.py               # python -m emovi_mcp
│   ├── main.py                   # Punto de entrada del servidor FastMCP
│   ├── config.py                 # Entorno, mapeos, constantes
│   ├── data_loader.py            # Cargador lazy de .dta con caché
│   ├── dictionary.py             # Diccionario de variables (JSON)
│   ├── stats_engine.py           # Matrices de transición, descriptivas
│   ├── data/
│   │   └── dictionary.json       # 792 variables
│   ├── helpers/
│   │   ├── formatting.py         # Formateadores Markdown para salida LLM
│   │   ├── labels.py             # Resolución de etiquetas de valor
│   │   ├── mobility_indices.py   # Shorrocks, Prais, razón de momios
│   │   ├── survey_variance.py    # Linealización de Taylor para SE/CI
│   │   ├── validation.py         # Validación de columnas y filtros
│   │   ├── visualization.py      # Heatmaps, Sankey, gráficas de barras
│   │   └── weights.py            # Media, mediana, cuantil, frecuencia ponderados
│   └── tools/
│       ├── __init__.py            # Registro de herramientas (11 tools)
│       ├── compare.py             # compare_groups
│       ├── describe.py            # describe_survey
│       ├── financial.py           # financial_inclusion_summary
│       ├── mobility.py            # transition_matrix
│       ├── stats.py               # weighted_stats
│       ├── subset.py              # filter_data
│       ├── tabulate.py            # tabulate
│       ├── temporal.py            # income_comparison
│       ├── variables.py           # list_variables, variable_detail
│       └── visualize.py           # visualize_mobility
└── tests/
    ├── conftest.py                # Fixtures compartidos (datos sintéticos)
    ├── test_dictionary.py
    ├── test_financial.py
    ├── test_mobility.py
    ├── test_mobility_indices.py
    ├── test_stats_engine.py
    ├── test_survey_variance.py
    ├── test_temporal.py
    ├── test_visualization.py
    └── test_wealth_index.py
```

## Licencia

MIT

## Agradecimientos

Datos de la encuesta: [Centro de Estudios Espinosa Yglesias (CEEY)](https://ceey.org.mx/) — ESRU-EMOVI 2023.
