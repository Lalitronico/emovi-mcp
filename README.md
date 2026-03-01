# emovi-mcp

[![CI](https://github.com/Lalitronico/emovi-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Lalitronico/emovi-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/emovi-mcp)](https://pypi.org/project/emovi-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/emovi-mcp)](https://pypi.org/project/emovi-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
git clone https://github.com/Lalitronico/emovi-mcp.git
cd emovi-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Optional: visualization support
pip install -e ".[dev,viz]"
```

Or install directly from PyPI:

```bash
pip install emovi-mcp
# With visualization support
pip install emovi-mcp[viz]
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

The server exposes 11 MCP tools:

| Tool | Description |
|------|-------------|
| `describe_survey` | Survey overview: datasets, sample size, design, dimensions |
| `list_variables` | Browse variables by dataset, section, or search keyword |
| `variable_detail` | Full info for a variable: label, values, section, dataset |
| `tabulate` | Weighted crosstabulation (row x col with expansion factors) |
| `transition_matrix` | Intergenerational mobility matrix with formal indices (Shorrocks, Prais, odds ratios) and optional standard errors via Taylor linearization |
| `weighted_stats` | Descriptive statistics: mean, median, std, quantiles (weighted) |
| `compare_groups` | Compare a variable across groups (mean, median, or distribution) |
| `filter_data` | Extract raw data rows with optional filters (max 100 rows) |
| `financial_inclusion_summary` | Financial inclusion analysis: savings, credit, banking, literacy, discrimination |
| `income_comparison` | Temporal income comparison between 2017 and 2023 with poverty line classification |
| `visualize_mobility` | Generate heatmaps, Sankey diagrams, or bar charts for mobility matrices (requires `[viz]`) |

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

All 96 tests cover weighted statistics, transition matrices, mobility indices, Taylor-linearized standard errors, financial inclusion, temporal income comparison, visualization, and variable dictionary functionality using synthetic data (no real microdata needed for tests).

## Technical Notes / Notas técnicas

- **All statistics are weighted** using the `factor` expansion variable (or `fac_inc` for the financial inclusion module)
- **pyreadstat loads .dta files with `apply_value_formats=False`** to avoid crashes from duplicate municipality labels
- **`padres_edu`** is constructed as `max(educp, educm)` following the CEEY .do file methodology
- **Wealth index** uses PCA on binary asset indicators (Filmer & Pritchett, 2001), as an alternative to CEEY's MCA approach
- **Standard errors** use Taylor linearization for ratio estimators under stratified cluster sampling (PSU/strata)
- **Mobility indices**: Shorrocks M, Prais escape probability, intergenerational Pearson r, corner odds ratios
- **STDIO transport**: The server communicates via standard input/output, compatible with Claude Desktop and other MCP clients

## Project Structure / Estructura del proyecto

```
emovi-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .github/workflows/
│   ├── ci.yml                    # CI: pytest on Python 3.10/3.11/3.12
│   └── publish.yml               # Publish to PyPI on release
├── scripts/
│   ├── build_dictionary.py       # One-time dictionary builder
│   └── validate_ceey.py          # Validate against CEEY 2025 reference
├── validation/
│   └── ceey_reference_values.json # CEEY reference matrices
├── src/emovi_mcp/
│   ├── __init__.py
│   ├── __main__.py               # python -m emovi_mcp
│   ├── main.py                   # FastMCP server entry point
│   ├── config.py                 # Environment, mappings, constants
│   ├── data_loader.py            # Lazy .dta loader with cache
│   ├── dictionary.py             # Variable dictionary (JSON-based)
│   ├── stats_engine.py           # Transition matrices, descriptives
│   ├── data/
│   │   └── dictionary.json       # 792 variables
│   ├── helpers/
│   │   ├── formatting.py         # Markdown formatters for LLM output
│   │   ├── labels.py             # Value label resolution
│   │   ├── mobility_indices.py   # Shorrocks, Prais, odds ratios
│   │   ├── survey_variance.py    # Taylor linearization for SE/CI
│   │   ├── validation.py         # Column + filter validation
│   │   ├── visualization.py      # Heatmaps, Sankey, bar charts
│   │   └── weights.py            # Weighted mean, median, quantile, freq
│   └── tools/
│       ├── __init__.py            # Tool registration (11 tools)
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
    ├── conftest.py                # Shared fixtures (synthetic data)
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

## License / Licencia

MIT

## Acknowledgments / Agradecimientos

Survey data: [Centro de Estudios Espinosa Yglesias (CEEY)](https://ceey.org.mx/) — ESRU-EMOVI 2023.
