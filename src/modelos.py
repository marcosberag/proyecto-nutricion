# --- BREAKFAST DETECTION CONFIG ---
KEYWORDS_BREAKFAST_YES = {
    'breakfast', 'brunch', 'pancakes', 'waffles', 'omelet', 'scramble',
    'cereal', 'morning', 'yogurt', 'oatmeal', 'granola', 'porridge',
    'toast', 'muffins', 'crepes', 'smoothie', 'coffee', 'latte', 'egg'
}

# --- BLACKLIST (NOT BREAKFAST) ---
KEYWORDS_BREAKFAST_NO = {
    # Meat & Fish
    'chicken', 'poultry', 'beef', 'steak', 'pork', 'lamb', 'sheep', 'meat',
    'fish', 'salmon', 'tuna', 'shrimp', 'seafood', 'cod', 'tilapia', 'halibut', 'crab',
    'burger', 'wings', 'thighs', 'roast', 'brisket', 'ribs', 'venison', 'duck',

    # Main dishes
    'dinner', 'supper', 'lunch', 'main-dish', 'soup', 'stew', 'chili', 'curry',
    'pasta', 'pizza', 'lasagna', 'spaghetti', 'noodle', 'ravioli', 'risotto',
    'casserole', 'taco', 'burrito', 'enchilada', 'quesadilla', 'sandwich',

    # Savory ingredients
    'onion', 'garlic', 'rice', 'potato', 'beans', 'gravy', 'soy', 'mustard',

    # Not real food (Mixes, pure desserts)
    'jello', 'dessert', 'cookie', 'cake', 'brownie', 'cupcake', 'frosting',
    'candy', 'snack', 'mix', 'seasoning', 'rub', 'sauce', 'dip'
}

# Cost estimation constants
BASE_COST = 0.50
PROTEIN_FACTOR = 0.035
FAT_FACTOR = 0.015
CARB_FACTOR = 0.005


class Recipe:
    def __init__(self, row):
        self.name = row['name']
        self.ingredients = row['ingredients']
        self.steps = row['steps']
        self.tags = row['tags']

        # Nutrition: [Calories, Fat, Sugar, Sodium, Protein, Sat_Fat, Carbs]
        self.nutrition = row['nutrition']
        self.calories = self.nutrition[0]
        self.protein_pdv = self.nutrition[4]
        self.fat_pdv = self.nutrition[1]
        self.carbs_pdv = self.nutrition[6]

        self.rating = row.get('avg_rating', 0.0)

    def is_breakfast(self):
        """ Determines if the recipe is suitable for breakfast. """
        tags_set = set(self.tags)
        name_lower = self.name.lower()

        # 1. Exclusion Filter
        if any(k in tags_set for k in KEYWORDS_BREAKFAST_NO): return False
        if any(k in name_lower for k in KEYWORDS_BREAKFAST_NO): return False

        # 2. Inclusion Filter
        if any(k in tags_set for k in KEYWORDS_BREAKFAST_YES): return True
        if any(k in name_lower for k in KEYWORDS_BREAKFAST_YES): return True

        return False

    def calculate_cost(self):
        cost_prot = self.protein_pdv * PROTEIN_FACTOR
        cost_fat = self.fat_pdv * FAT_FACTOR
        cost_carb = self.carbs_pdv * CARB_FACTOR
        return round(BASE_COST + cost_prot + cost_fat + cost_carb, 2)

    def get_cost_symbol(self):
        cost = self.calculate_cost()
        if cost <= 3.5:
            return "$"
        elif cost <= 10:
            return "$$"
        return "$$$"

    def show_full_details(self):
        """ Prints the recipe card to console. """
        symbol = self.get_cost_symbol()
        stars = "★" * int(round(self.rating)) if self.rating else "N/A"
        type_lbl = "☕ BREAKFAST" if self.is_breakfast() else "🍽️ MAIN DISH"

        print("\n" + "=" * 60)
        print(f" {type_lbl}")
        print(f" RECIPE: {self.name.upper()}")
        print("=" * 60)
        print(f" 💰 Est. Cost: {symbol} ({self.calculate_cost()} u.)")
        print(f" ⭐ Rating: {self.rating:.2f}/5.0 {stars}")
        print("-" * 60)
        print(f" 📊 NUTRITION PER SERVING:")
        print(f"    - Calories: {self.calories} kcal")
        print(f"    - Protein:  {self.protein_pdv}% DV")
        print(f"    - Fat:      {self.fat_pdv}% DV")
        print(f"    - Carbs:    {self.carbs_pdv}% DV")
        print("-" * 60)
        print(f" 🛒 INGREDIENTS ({len(self.ingredients)}):")
        for ing in self.ingredients:
            print(f"    • {ing}")
        print("-" * 60)
        print(" 👨‍🍳 INSTRUCTIONS:")
        for i, step in enumerate(self.steps, 1):
            print(f"   {i}. {step}")
        print("=" * 60 + "\n")