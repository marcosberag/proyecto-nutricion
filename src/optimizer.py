"""Módulo de optimización de menús semanales.

Implementa el algoritmo de scoring multicriterio para seleccionar
las recetas más adecuadas según el perfil nutricional del usuario.

Fórmula de scoring:
    S(r) = w_p * P(r) - w_f * F(r) - w_c * C(r) + w_r * R(r)
    
Donde:
    - P(r) = % valor diario de proteína
    - F(r) = % valor diario de grasa
    - C(r) = coste estimado
    - R(r) = rating medio de usuarios
    - w_i = pesos específicos del perfil

References:
    - OMS: Dietary Guidelines (umbrales calóricos)
    - Phillips & Van Loon (2011): Protein for athletes (perfil fitness)
"""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modelos import Recipe


class Optimizer:
    """
    Optimizador de menús semanales basado en scoring multicriterio.
    
    Attributes:
        recipes: Lista de objetos Recipe disponibles para selección.
        
    Perfiles soportados:
        - 'budget': Minimiza coste
        - 'fitness': Maximiza proteína, minimiza grasa
        - 'gourmet': Maximiza rating de usuarios
        - 'balanced': Equilibrio entre proteína, grasa y coste
    """
    def __init__(self, recipe_list):
        self.recipes = recipe_list

    def _calculate_score(self, recipe: 'Recipe', profile: str) -> float:
        """
        Calcula el score de una receta según el perfil nutricional.
        
        Args:
            recipe: Objeto Recipe a evaluar.
            profile: Perfil del usuario ('budget', 'fitness', 'gourmet', 'balanced').
            
        Returns:
            Score numérico. Mayor = mejor para el perfil dado.
            
        Notes:
            Pesos del scoring:
            - budget: prioriza bajo coste
            - fitness: w_p=3.0, w_f=1.5, w_c=0.5 (proteína alta, grasa baja)
            - gourmet: w_r=20.0 (solo rating)
            - balanced: w_p=1.0, w_f=0.5, w_c=2.0 (equilibrado)
        """
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

    def replace_recipe(
        self,
        old_recipe: 'Recipe',
        current_menu: list['Recipe']
    ) -> 'Recipe | None':
        """
        Encuentra un sustituto para una receta manteniendo el tipo de comida.
        
        Args:
            old_recipe: Receta a reemplazar.
            current_menu: Menú actual (para evitar duplicados).
            
        Returns:
            Nueva receta del mismo tipo (desayuno/principal) que no esté
            en el menú actual, o None si no hay candidatos.
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

    def _select_best(
        self,
        pool: list['Recipe'],
        profile: str,
        n: int
    ) -> list['Recipe']:
        """
        Selecciona las n mejores recetas de un pool según el perfil.
        
        Args:
            pool: Lista de recetas candidatas.
            profile: Perfil nutricional del usuario.
            n: Número de recetas a seleccionar.
            
        Returns:
            Lista de n recetas seleccionadas aleatoriamente del top 100.
            
        Notes:
            1. Calcula score para cada receta
            2. Ordena por score descendente (desempate: menos pasos)
            3. Toma el top 100
            4. Selecciona n aleatorias del top para variedad
        """
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

    def generate_structured_menu(self, profile: str) -> list['Recipe']:
        """
        Genera un menú semanal estructurado (7 días x 3 comidas).
        
        Args:
            profile: Perfil nutricional ('budget', 'fitness', 'gourmet', 'balanced').
            
        Returns:
            Lista de 21 recetas ordenadas: [D1_desayuno, D1_almuerzo, D1_cena,
            D2_desayuno, ...]. Índice % 3: 0=desayuno, 1=almuerzo, 2=cena.
            
        Notes:
            - Separa recetas en pool de desayunos y pool de principales
            - Selecciona las 7 mejores de cada pool según el perfil
            - Si no hay suficientes desayunos, usa principales como fallback
        """
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