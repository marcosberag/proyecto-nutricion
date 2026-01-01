from collections import Counter


def get_shopping_list_obj(menu_recipes):
    all_ingredients = []
    for r in menu_recipes:
        all_ingredients.extend(r.ingredients)
    return Counter(all_ingredients)


def print_shopping_list(menu_recipes):
    counts = get_shopping_list_obj(menu_recipes)

    print(f"\n🛒 --- SHOPPING LIST ({len(menu_recipes)} meals) ---")

    for ingredient, qty in counts.most_common(30):
        print(f" [ ] {ingredient} (x{qty})")

    remaining = len(counts) - 30
    if remaining > 0:
        print(f"... and {remaining} other items.")