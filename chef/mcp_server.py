"""Local MCP server with deterministic recipe scaling."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("culinary-tools")

@mcp.tool()
def scale_recipe(ingredients: list[dict], from_servings: float, to_servings: float) -> list[dict]:
    """Scale ingredient quantities; each ingredient has name, quantity and unit."""
    if from_servings <= 0 or to_servings <= 0:
        raise ValueError("Serving counts must be positive")
    result = []
    for item in ingredients:
        amount = float(item["quantity"])
        if amount < 0:
            raise ValueError("Ingredient quantities cannot be negative")
        result.append({**item, "quantity": round(amount * to_servings / from_servings, 3)})
    return result

if __name__ == "__main__":
    mcp.run(transport="stdio")
