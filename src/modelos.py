"""Módulo de modelos de datos para recetas.

Contiene la clase Recipe que encapsula toda la información
de una receta y proporciona métodos para clasificación,
estimación de costes y visualización.

References:
    Clasificación de desayunos basada en análisis de tags del dataset Food.com.
    Estimación de costes basada en aproximación lineal por macronutrientes.
"""

from typing import Any

# --- BREAKFAST DETECTION CONFIG ---
# Keywords que indican que una receta ES un desayuno
KEYWORDS_BREAKFAST_YES = {
    'breakfast', 'brunch', 'pancakes', 'waffles', 'omelet', 'scramble',
    'cereal', 'morning', 'yogurt', 'oatmeal', 'granola', 'porridge',
    'toast', 'muffins', 'crepes', 'smoothie', 'coffee', 'latte', 'egg'
}

# Keywords que indican que una receta NO es un desayuno (blacklist)
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

# Constantes para estimación de coste (en unidades monetarias arbitrarias)
# Fórmula: C(r) = BASE + PROTEIN_FACTOR*P + FAT_FACTOR*F + CARB_FACTOR*Carb
# Justificación: alimentos ricos en proteína (carnes, pescados) suelen ser más caros
BASE_COST = 0.50        # Coste base por receta
PROTEIN_FACTOR = 0.035  # Factor de coste por % DV de proteína
FAT_FACTOR = 0.015      # Factor de coste por % DV de grasa
CARB_FACTOR = 0.005     # Factor de coste por % DV de carbohidratos


class Recipe:
    """
    Representa una receta con su información nutricional y métodos auxiliares.
    
    Attributes:
        name: Nombre de la receta.
        ingredients: Lista de ingredientes.
        steps: Lista de pasos de preparación.
        tags: Lista de etiquetas/categorías.
        nutrition: Lista [calories, fat, sugar, sodium, protein, sat_fat, carbs].
        calories: Calorías totales de la receta.
        protein_pdv: Porcentaje del valor diario de proteína.
        fat_pdv: Porcentaje del valor diario de grasa.
        carbs_pdv: Porcentaje del valor diario de carbohidratos.
        rating: Valoración media de usuarios (0-5).
    """
    
    def __init__(self, row: dict[str, Any]) -> None:
        """
        Inicializa una receta a partir de una fila del DataFrame.
        
        Args:
            row: Diccionario o Series con los datos de la receta.
        """
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

    def is_breakfast(self) -> bool:
        """
        Determina si la receta es apropiada para el desayuno.
        
        Utiliza un sistema de dos fases:
        1. Filtro de exclusión: si contiene keywords de comidas principales, retorna False
        2. Filtro de inclusión: si contiene keywords de desayuno, retorna True
        
        Returns:
            True si la receta es apta para desayuno, False en caso contrario.
        """
        tags_set = set(self.tags)
        name_lower = self.name.lower()

        # 1. Exclusion Filter
        if any(k in tags_set for k in KEYWORDS_BREAKFAST_NO): return False
        if any(k in name_lower for k in KEYWORDS_BREAKFAST_NO): return False

        # 2. Inclusion Filter
        if any(k in tags_set for k in KEYWORDS_BREAKFAST_YES): return True
        if any(k in name_lower for k in KEYWORDS_BREAKFAST_YES): return True

        return False

    def calculate_cost(self) -> float:
        """
        Estima el coste de la receta basado en macronutrientes.
        
        Fórmula: C = BASE_COST + PROTEIN_FACTOR*P + FAT_FACTOR*F + CARB_FACTOR*Carb
        
        Returns:
            Coste estimado en unidades monetarias arbitrarias.
            
        Notes:
            Esta es una aproximación. Los alimentos ricos en proteína
            (carnes, pescados, lácteos) tienden a ser más caros.
        """
        cost_prot = self.protein_pdv * PROTEIN_FACTOR
        cost_fat = self.fat_pdv * FAT_FACTOR
        cost_carb = self.carbs_pdv * CARB_FACTOR
        return round(BASE_COST + cost_prot + cost_fat + cost_carb, 2)

    def get_cost_symbol(self) -> str:
        """
        Devuelve un símbolo visual del nivel de coste.
        
        Returns:
            '$' si coste <= 3.5, '$$' si <= 10, '$$$' en otro caso.
        """
        cost = self.calculate_cost()
        if cost <= 3.5:
            return "$"
        elif cost <= 10:
            return "$$"
        return "$$$"

    def show_full_details(self) -> None:
        """
        Imprime en consola la ficha completa de la receta.
        
        Incluye: tipo de comida, nombre, coste estimado, rating,
        información nutricional, lista de ingredientes y pasos.
        """
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