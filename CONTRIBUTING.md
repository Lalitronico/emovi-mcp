# Contributing to emovi-mcp / Contribuir a emovi-mcp

Thank you for your interest in contributing! / ¡Gracias por tu interés en contribuir!

## Getting started / Primeros pasos

```bash
git clone https://github.com/your-user/emovi-mcp.git
cd emovi-mcp
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -e ".[dev,viz]"
```

## Running tests / Ejecutar pruebas

```bash
pytest -v
```

All tests use synthetic data — no real ESRU-EMOVI microdata is needed to run the test suite.

Todas las pruebas usan datos sintéticos — no se necesitan microdatos reales para ejecutar las pruebas.

## Code style / Estilo de código

- Python 3.10+ with type hints where they improve clarity
- Variable names and docstrings in English
- Comments may be bilingual (English/Spanish) where helpful
- Use `pathlib` over `os.path`
- Use f-strings over `.format()`

## Adding a new MCP tool / Agregar una nueva herramienta MCP

1. Create a new module in `src/emovi_mcp/tools/`
2. Implement a `register(mcp)` function that uses `@mcp.tool()`
3. Import and call `register` from `src/emovi_mcp/tools/__init__.py`
4. Add tests in `tests/` using synthetic DataFrames (see `conftest.py` for examples)
5. Update the tools table in `README.md`

## Adding a new statistical helper

1. Add the function to `src/emovi_mcp/stats_engine.py` or create a module under `src/emovi_mcp/helpers/`
2. All statistics must be weighted (use the `factor` expansion variable)
3. Add unit tests with known expected values

## Reporting issues / Reportar problemas

Please include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior

## License / Licencia

By contributing, you agree that your contributions will be licensed under the MIT License.

Al contribuir, aceptas que tus contribuciones serán licenciadas bajo la Licencia MIT.
