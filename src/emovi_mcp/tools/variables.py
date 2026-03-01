"""Tools: list_variables, variable_detail — browse the data dictionary."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from emovi_mcp.data_loader import get_metadata
from emovi_mcp.dictionary import (
    get_variable_info,
    list_all_variables,
    list_sections,
    search_variables,
)


def register(mcp: FastMCP):
    @mcp.tool()
    def list_variables(
        dataset: str = "entrevistado",
        section: str | None = None,
        search: str | None = None,
    ) -> str:
        """List available variables in the survey.

        Args:
            dataset: Which dataset to list variables from.
                     Options: entrevistado, hogar, inclusion_financiera.
            section: Filter by questionnaire section (optional).
            search: Search term to filter by variable name or description (optional).

        Returns a list of variables with their labels.
        """
        if search:
            results = search_variables(search, dataset=dataset)
        else:
            results = list_all_variables(dataset=dataset, section=section)

        if not results:
            # Fallback: try from .dta metadata
            try:
                meta = get_metadata(dataset)
                vl = meta["variable_labels"]
                results = [
                    {"name": k, "label": v, "dataset": dataset, "section": ""}
                    for k, v in vl.items()
                ]
                if search:
                    q = search.lower()
                    results = [
                        r for r in results
                        if q in r["name"].lower() or q in r["label"].lower()
                    ]
            except Exception:
                return f"No variables found for dataset={dataset!r}, section={section!r}, search={search!r}"

        lines = [f"## Variables in `{dataset}`"]
        if section:
            lines[0] += f" (section: {section})"
        if search:
            lines[0] += f" (search: {search!r})"
        lines.append(f"\n*{len(results)} variables found*\n")

        # Show as compact table
        lines.append("| Variable | Description |")
        lines.append("| --- | --- |")
        for r in results[:100]:  # Cap at 100
            lines.append(f"| `{r['name']}` | {r['label']} |")

        if len(results) > 100:
            lines.append(f"\n*... and {len(results) - 100} more. Use `search` to narrow.*")

        return "\n".join(lines)

    @mcp.tool()
    def variable_detail(variable: str) -> str:
        """Get detailed information about a specific variable.

        Args:
            variable: The variable name (e.g., 'educ', 'ingc_pc', 'sexo').

        Returns the variable label, value labels, dataset, and section.
        """
        info = get_variable_info(variable)

        if not info:
            # Try fallback from .dta metadata
            for ds_name in ["entrevistado", "hogar", "inclusion_financiera"]:
                try:
                    meta = get_metadata(ds_name)
                    if variable in meta["variable_labels"]:
                        info = {
                            "label": meta["variable_labels"][variable],
                            "dataset": ds_name,
                            "section": "",
                        }
                        # Check value labels
                        vl = meta["value_labels"]
                        for label_set_name, label_map in vl.items():
                            # Heuristic: label set name often matches or contains variable name
                            if variable in label_set_name.lower():
                                info["value_labels"] = {
                                    str(int(k)): v for k, v in label_map.items()
                                }
                                break
                        break
                except Exception:
                    continue

        if not info:
            return f"Variable `{variable}` not found in the dictionary. Use `list_variables(search=...)` to search."

        lines = [
            f"## Variable: `{variable}`",
            "",
            f"- **Label**: {info.get('label', 'N/A')}",
            f"- **Dataset**: {info.get('dataset', 'N/A')}",
            f"- **Section**: {info.get('section', 'N/A')}",
        ]

        value_labels = info.get("value_labels")
        if value_labels:
            lines.extend(["", "### Value labels", ""])
            lines.append("| Code | Label |")
            lines.append("| --- | --- |")
            for code in sorted(value_labels.keys(), key=lambda x: int(x) if x.lstrip("-").isdigit() else 0):
                lines.append(f"| {code} | {value_labels[code]} |")

        return "\n".join(lines)
