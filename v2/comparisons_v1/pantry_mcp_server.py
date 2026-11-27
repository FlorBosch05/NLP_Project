"""Standalone, read-only example resource and deterministic scaling tool."""
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

server = FastMCP('pantry-comparison')

@server.resource('pantry://inventory')
def pantry_inventory() -> str:
    """Read the current synthetic example inventory from disk."""
    path = Path(__file__).with_name('pantry_example.json')
    return json.dumps(json.loads(path.read_text(encoding='utf-8')), ensure_ascii=False)

@server.tool()
def scale_amount(amount: float, from_servings: float, to_servings: float) -> float:
    """Scale one non-negative amount between positive serving counts."""
    import math
    if not all(math.isfinite(x) for x in (amount, from_servings, to_servings)) or amount < 0 or from_servings <= 0 or to_servings <= 0:
        raise ValueError('Use finite non-negative amounts and positive serving counts')
    return round(amount * to_servings / from_servings, 3)

if __name__ == '__main__':
    server.run(transport='stdio')
