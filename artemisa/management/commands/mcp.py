"""Run Artemisa as a read-only MCP server over stdio.

    python manage.py mcp

Connect it from Claude Desktop or Claude Code (see readme.md) and ask things like
"who is leading Recurve Bow Women in the demo?". It reads whatever database `.env`
points at; every tool only reads, and none of them calls the Anthropic API.
"""
from django.core.management.base import BaseCommand

from artemisa import mcp_tools

INSTRUCTIONS = (
    "Read-only access to Artemisa, a scoring system for archery tournaments. "
    "Start with list_competitions to get competition ids. Scoring: X counts 10 points "
    "and also counts as an X; M is a miss (0). Ties are broken by number of 10s "
    "(X included), then Xs, then the points of the last end."
)


def build_server():
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    server = MCPServer("artemisa", instructions=INSTRUCTIONS)
    read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)

    @server.tool(annotations=read_only)
    def list_competitions() -> dict:
        """List every competition (newest first): id, name, date, location, whether it is the
        public demo, and its categories with how many archers are registered in each."""
        return {"competitions": mcp_tools.list_competitions()}

    @server.tool(annotations=read_only)
    def get_leaderboard(competition_id: int, category: str | None = None) -> dict:
        """Ranked archers with total score, 10s, Xs and last-end points.
        `category` is optional: a category name or code (e.g. "RW" or "Recurve Bow Women");
        leave it out to get every category."""
        return mcp_tools.get_leaderboard(competition_id, category)

    @server.tool(annotations=read_only)
    def get_archer_scorecard(competition_id: int, archer_name: str) -> dict:
        """One archer's arrows end by end, with end totals, running total and rank.
        `archer_name` can be part of the name, as long as it matches only one archer."""
        return mcp_tools.get_archer_scorecard(competition_id, archer_name)

    @server.tool(annotations=read_only)
    def get_match_recap(competition_id: int) -> dict:
        """The saved AI-written recap of a competition, if one matches the current standings.
        Returns recap = null otherwise; this tool never generates a new one."""
        return mcp_tools.get_match_recap(competition_id)

    return server


class Command(BaseCommand):
    help = "Run the read-only Artemisa MCP server over stdio (for Claude Desktop / Claude Code)."

    def handle(self, *args, **options):
        # stdout carries the MCP protocol: nothing else may be printed there.
        build_server().run("stdio")
