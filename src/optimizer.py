import random


class Optimizer:
    def __init__(self, recipe_list):
        self.recipes = recipe_list

    def _calculate_score(self, recipe, profile):
        score = 0.0
        cost = recipe.calculate_cost()

        # Scoring logic based on profile
        if profile == "budget":
            if cost > 0: score = (10 / cost) * 5
            if recipe.calories < 200: score -= 10
        elif profile == "fitness":
            score = (recipe.protein_pdv * 3) - (recipe.fat_pdv * 1.5) - (cost * 0.5)
        elif profile == "gourmet":
            score = recipe.rating * 20
            if recipe.calories > 400: score += 5
        elif profile == "balanced":
            score = recipe.protein_pdv - (recipe.fat_pdv * 0.5) - (cost * 2)

        return score

    def replace_recipe(self, old_recipe, current_menu):
        """
        Finds a new recipe of the SAME TYPE (Breakfast/Main)
        that is not currently in the menu.
        """
        is_breakfast = old_recipe.is_breakfast()
        used_names = {r.name for r in current_menu}

        candidates = []
        for r in self.recipes:
            if r.is_breakfast() == is_breakfast:
                if r.name not in used_names:
                    candidates.append(r)

        if not candidates:
            return None

        return random.choice(candidates)

    def _select_best(self, pool, profile, n):
        candidates = []
        for r in pool:
            if r.calories == 0: continue
            score = self._calculate_score(r, profile)
            # Tuple: (Score, Steps (fewer is better), Recipe)
            candidates.append((score, len(r.steps), r))

        # Sort desc
        candidates.sort(key=lambda x: (x[0], -x[1]), reverse=True)

        # Top 100 pool
        top_tier = [item[2] for item in candidates[:100]]

        if len(top_tier) < n: return top_tier
        return random.sample(top_tier, n)

    def generate_structured_menu(self, profile):
        print(f"🧠 OPTIMIZER: Structuring week for '{profile}'...")

        pool_breakfast = [r for r in self.recipes if r.is_breakfast()]
        pool_main = [r for r in self.recipes if not r.is_breakfast()]

        print(f"   - Breakfasts available: {len(pool_breakfast)}")
        print(f"   - Mains available: {len(pool_main)}")

        best_breakfasts = self._select_best(pool_breakfast, profile, 7)
        best_mains = self._select_best(pool_main, profile, 14)

        # Fallback if not enough breakfasts
        if len(best_breakfasts) < 7:
            needed = 7 - len(best_breakfasts)
            best_breakfasts.extend(random.sample(pool_main, needed))

        menu = []
        for i in range(7):
            menu.append(best_breakfasts[i])  # Breakfast
            menu.append(best_mains[i * 2])  # Lunch
            menu.append(best_mains[i * 2 + 1])  # Dinner

        return menu