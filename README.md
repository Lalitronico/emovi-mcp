# emovi-mcp

MCP server for the ESRU-EMOVI 2023 social mobility survey (Mexico).

Servidor MCP para la encuesta ESRU-EMOVI 2023 de movilidad social en México.

---

## What is this? / ¿Qué es esto?

**emovi-mcp** lets AI assistants (Claude, ChatGPT, etc.) query Mexico's most comprehensive social mobility survey through natural language. It exposes weighted statistical computations, intergenerational transition matrices, and variable exploration as MCP tools.

**emovi-mcp** permite que asistentes de IA (Claude, ChatGPT, etc.) consulten la encuesta de movilidad social más completa de México mediante lenguaje natural. Expone cómputos estadísticos ponderados, matrices de transición intergeneracional y exploración de variables como herramientas MCP.

## About ESRU-EMOVI 2023

The ESRU-EMOVI 2023 survey, conducted by the Centro de Estudios Espinosa Yglesias (CEEY), is a nationally representative survey of social mobility in Mexico. It covers 17,843 respondents aged 25-64, with expansion factors representing ~60 million people.

**Datasets included:**
| Dataset | Description | Rows | Variables |
|---------|-------------|------|-----------|
| `entrevistado` | Main respondent data | 17,843 | ~296 |
| `hogar` | Household roster | 55,477 | ~56 |
| `ingreso_2017` | Imputed 2017 income (temporal comparison) | 17,665 | ~2 |
| `inclusion_financiera` | Financial inclusion module | 5,976 | ~109 |

## Installation / Instalación

```bash
# Clone the repository
git clone https://github.com/your-user/emovi-mcp.git
cd emovi-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Prerequisites / Prerrequisitos

- Python >= 3.10
- ESRU-EMOVI 2023 .dta files (obtain from [CEEY](https://ceey.org.mx/emovi/))

## Configuration / Configuración

Set the `EMOVI_DATA_DIR` environment variable to point to the directory containing the .dta files:

```bash
# Linux/Mac
export EMOVI_DATA_DIR="/path/to/Esru Emovi 2023/_extracted/3 BASES DE DATOS/Data"

# Windows (PowerShell)
$env:EMOVI_DATA_DIR = "C:\path\to\Esru Emovi 2023\_extracted\3 BASES DE DATOS\Data"

# Windows (cmd)
set EMOVI_DATA_DIR=C:\path\to\Esru Emovi 2023\_extracted\3 BASES DE DATOS\Data
```

## Usage with Claude Desktop / Uso con Claude Desktop

Add the following to your `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "emovi-mcp": {
      "command": "C:/path/to/emovi-mcp/.venv/Scripts/python.exe",
      "args": ["-m", "emovi_mcp"],
      "env": {
        "EMOVI_DATA_DIR": "C:/path/to/3 BASES DE DATOS/Data"
      }
    }
  }
}
```

On macOS/Linux, replace `Scripts/python.exe` with `bin/python`.

## Tools / Herramientas

The server exposes 8 MCP tools:

| Tool | Description |
|------|-------------|
| `describe_survey` | Survey overview: datasets, sample size, design, dimensions |
| `list_variables` | Browse variables by dataset, section, or search keyword |
| `variable_detail` | Full info for a variable: label, values, section, dataset |
| `tabulate` | Weighted crosstabulation (row × col with expansion factors) |
| `transition_matrix` | Intergenerational mobility matrix (education, occupation, income) |
| `weighted_stats` | Descriptive statistics: mean, median, std, quantiles (weighted) |
| `compare_groups` | Compare a variable across groups (mean, median, or distribution) |
| `filter_data` | Extract raw data rows with optional filters (max 100 rows) |

### Example queries / Ejemplos de consultas

Once connected, you can ask the AI assistant questions like:

- *"¿Cuál es la distribución educativa por sexo?"*
  → Uses `tabulate(row_var="educ", col_var="sexo")`

- *"Muéstrame la matriz de movilidad educativa intergeneracional"*
  → Uses `transition_matrix(dimension="education")`

- *"¿Cuál es el ingreso promedio por región?"*
  → Uses `weighted_stats(variable="ingc_pc", by="region_14")`

- *"Compara la movilidad educativa entre hombres y mujeres"*
  → Uses `transition_matrix(dimension="education", by="sexo")`

- *"¿Qué variables hay sobre educación?"*
  → Uses `list_variables(search="educ")`

## Variable Dictionary / Diccionario de variables

The project includes a pre-built dictionary with 792 variables extracted from the official CEEY documentation and .dta metadata. The dictionary supports searching by name, description, dataset, and section.

To rebuild the dictionary from source data:

```bash
python scripts/build_dictionary.py
```

This requires the `Diccionario ESRU EMOVI 2023.xlsx` file in the data directory.

## Running Tests / Ejecutar pruebas

```bash
pytest
```

All 23 tests cover weighted statistics, transition matrix computation, and variable dictionary functionality using synthetic data (no real microdata needed for tests).

## Technical Notes / Notas técnicas

- **All statistics are weighted** using the `factor` expansion variable from the survey design
- **pyreadstat loads .dta files with `apply_value_formats=False`** to avoid crashes from duplicate municipality labels
- **`padres_edu`** is constructed as `max(educp, educm)` following the CEEY .do file methodology
- **Income quintiles** are computed using weighted quantile allocation (replicating Stata's `xtile [pw=factor]`)
- **STDIO transport**: The server communicates via standard input/output, compatible with Claude Desktop and other MCP clients

## Project Structure / Estructura del proyecto

```
emovi-mcp/
├── pyproject.toml
├── README.md
├── scripts/
│   └── build_dictionary.py      # One-time dictionary builder
├── src/emovi_mcp/
│   ├── __init__.py
│   ├── __main__.py              # python -m emovi_mcp
│   ├── main.py                  # FastMCP server entry point
│   ├── config.py                # Environment, mappings, constants
│   ├── data_loader.py           # Lazy .dta loader with cache
│   ├── dictionary.py            # Variable dictionary (JSON-based)
│   ├── stats_engine.py          # Transition matrices, descriptives
│   ├── data/
│   │   └── dictionary.json      # 792 variables
│   ├── helpers/
│   │   ├── formatting.py        # Markdown formatters for LLM output
│   │   ├── labels.py            # Value label resolution
│   │   ├── validation.py        # Column + filter validation
│   │   └── weights.py           # Weighted mean, median, quantile, freq
│   └── tools/
│       ├── __init__.py           # Tool registration
│       ├── compare.py            # compare_groups
│       ├── describe.py           # describe_survey
│       ├── mobility.py           # transition_matrix
│       ├── stats.py              # weighted_stats
│       ├── subset.py             # filter_data
│       ├── tabulate.py           # tabulate
│       └── variables.py          # list_variables, variable_detail
└── tests/
    ├── conftest.py               # Shared fixtures (synthetic data)
    ├── test_dictionary.py
    ├── test_mobility.py
    └── test_stats_engine.py
```

## License / Licencia

MIT

## Acknowledgments / Agradecimientos

Survey data: [Centro de Estudios Espinosa Yglesias (CEEY)](https://ceey.org.mx/) — ESRU-EMOVI 2023.
