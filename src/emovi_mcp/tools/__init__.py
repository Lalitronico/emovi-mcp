"""MCP tool registration."""

from emovi_mcp.tools.describe import register as register_describe
from emovi_mcp.tools.variables import register as register_variables
from emovi_mcp.tools.tabulate import register as register_tabulate
from emovi_mcp.tools.mobility import register as register_mobility
from emovi_mcp.tools.stats import register as register_stats
from emovi_mcp.tools.compare import register as register_compare
from emovi_mcp.tools.subset import register as register_subset
from emovi_mcp.tools.financial import register as register_financial
from emovi_mcp.tools.temporal import register as register_temporal
from emovi_mcp.tools.visualize import register as register_visualize


def register_tools(mcp):
    """Register all tools with the MCP server."""
    register_describe(mcp)
    register_variables(mcp)
    register_tabulate(mcp)
    register_mobility(mcp)
    register_stats(mcp)
    register_compare(mcp)
    register_subset(mcp)
    register_financial(mcp)
    register_temporal(mcp)
    register_visualize(mcp)
