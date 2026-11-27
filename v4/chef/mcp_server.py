"""Deterministic recipe tools exposed through MCP over stdio."""
import math
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("flavor-chef-v2")

@mcp.tool()
def scale_recipe(ingredients: list[dict], from_servings: float, to_servings: float) -> list[dict]:
    """Scale linear ingredients, preserve fixed amounts and flag unspecified damped scaling."""
    if not all(math.isfinite(x) and x > 0 for x in (from_servings, to_servings)):
        raise ValueError("Serving counts must be finite and positive")
    if not ingredients:
        raise ValueError("At least one ingredient is required")
    result = []
    for item in ingredients:
        rule = item.get("scaling", "linear")
        raw_amount = item.get("quantity")
        if rule not in {"linear", "fixed", "damped"}:
            raise ValueError("Unknown scaling rule")
        if raw_amount is None:
            result.append({"name": str(item["name"]), "quantity": None, "unit": str(item["unit"]), "status": "No numeric source quantity; adjust to taste or follow the recipe."})
            continue
        amount = float(raw_amount)
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("Quantities must be finite and non-negative")
        if rule == "damped":
            result.append({"name": str(item["name"]), "quantity": None, "unit": str(item["unit"]), "original_quantity": amount, "status": "Source requests damped scaling but provides no formula; adjust manually."})
            continue
        result.append({"name": str(item["name"]), "quantity": round(amount * to_servings / from_servings, 3) if rule == "linear" else amount, "unit": str(item["unit"]), "status": rule})
    return result

@mcp.tool()
def convert_units(amount: float, from_unit: str, to_unit: str) -> dict:
    """Convert within mass or volume, never mass to volume."""
    factors = {"g": ("mass", 1), "kg": ("mass", 1000), "mg": ("mass", .001),
               "ml": ("volume", 1), "l": ("volume", 1000), "tsp": ("volume", 5), "tbsp": ("volume", 15)}
    aliases = {'gram':'g','grams':'g','gramme':'g','grammes':'g','kilogram':'kg','kilograms':'kg', 'milligram':'mg','milligrams':'mg', 'milliliter':'ml','milliliters':'ml','millilitre':'ml','millilitres':'ml','liter':'l','liters':'l','litre':'l','litres':'l','teaspoon':'tsp','teaspoons':'tsp','tablespoon':'tbsp','tablespoons':'tbsp', 'grammen':'g','kilogrammen':'kg','liter':'l','milliliter':'ml','theelepel':'tsp','eetlepel':'tbsp'}
    a, b = from_unit.lower().strip(), to_unit.lower().strip()
    a, b = aliases.get(a, a), aliases.get(b, b)
    if not math.isfinite(amount) or amount < 0:
        raise ValueError("Amount must be finite and non-negative")
    if a not in factors or b not in factors or factors[a][0] != factors[b][0]:
        raise ValueError("Use supported units of the same dimension; mass-to-volume needs ingredient density")
    return {"amount": round(amount * factors[a][1] / factors[b][1], 6), "unit": b}

if __name__ == "__main__":
    mcp.run(transport="stdio")
