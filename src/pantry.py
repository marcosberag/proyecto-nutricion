"""Módulo de generación de lista de la compra.

Agrega los ingredientes de todas las recetas del menú
y genera una lista consolidada para facilitar la compra.
"""

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modelos import Recipe


def get_shopping_list_obj(menu_recipes: list['Recipe']) -> Counter:
    """
    Genera un contador de ingredientes a partir del menú.
    
    Args:
        menu_recipes: Lista de recetas del menú semanal.
        
    Returns:
        Counter con ingredientes como claves y cantidad de apariciones como valores.
    """
    all_ingredients = []
    for r in menu_recipes:
        all_ingredients.extend(r.ingredients)
    return Counter(all_ingredients)


def print_shopping_list(menu_recipes: list['Recipe']) -> None:
    """
    Imprime la lista de la compra formateada en consola.
    
    Args:
        menu_recipes: Lista de recetas del menú semanal.
        
    Notes:
        Muestra los 30 ingredientes más frecuentes con su cantidad.
        Si hay más de 30, indica cuántos adicionales hay.
    """
    counts = get_shopping_list_obj(menu_recipes)

    print(f"\n🛒 --- SHOPPING LIST ({len(menu_recipes)} meals) ---")

    for ingredient, qty in counts.most_common(30):
        print(f" [ ] {ingredient} (x{qty})")

    remaining = len(counts) - 30
    if remaining > 0:
        print(f"... and {remaining} other items.")