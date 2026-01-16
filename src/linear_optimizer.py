"""Optimizador de menús mediante Programación Lineal Entera Mixta (MILP).

Este módulo implementa la selección óptima de menús semanales como un problema
de optimización combinatoria con restricciones nutricionales.

Formulación matemática:
    max  Σ x_i · score_i           (maximizar score total)
    s.t. Σ x_i · cal_i ≤ CalMax    (límite calórico)
         Σ x_i · prot_i ≥ ProtMin  (mínimo proteína)
         Σ x_i (desayunos) = 7     (exactamente 7 desayunos)
         Σ x_i (principales) = 14  (exactamente 14 principales)
         x_i ∈ {0, 1}              (variables binarias)

El problema es NP-hard, pero scipy.optimize.milp usa el algoritmo
branch-and-bound con relajación LP para encontrar el óptimo global.

References:
    - Dantzig, G. B. (1963). Linear Programming and Extensions. Princeton UP.
    - scipy.optimize.milp documentation: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html
"""

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modelos import Recipe


class LinearOptimizer:
    """
    Optimizador de menús usando Programación Lineal Entera Mixta.
    
    A diferencia del Optimizer básico (heurístico), este garantiza
    encontrar el menú óptimo global sujeto a las restricciones.
    
    Attributes:
        recipes: Lista de recetas candidatas.
        breakfast_indices: Índices de recetas clasificadas como desayuno.
        main_indices: Índices de recetas clasificadas como comida principal.
    """
    
    def __init__(self, recipe_list: list['Recipe']) -> None:
        """
        Inicializa el optimizador lineal.
        
        Args:
            recipe_list: Lista de objetos Recipe candidatos.
        """
        self.recipes = recipe_list
        self.n = len(recipe_list)
        
        # Pre-calcular índices de desayunos y principales
        self.breakfast_indices = [i for i, r in enumerate(recipe_list) if r.is_breakfast()]
        self.main_indices = [i for i, r in enumerate(recipe_list) if not r.is_breakfast()]
        
        print(f"🔢 LinearOptimizer initialized:")
        print(f"   - Total recipes: {self.n}")
        print(f"   - Breakfasts: {len(self.breakfast_indices)}")
        print(f"   - Main dishes: {len(self.main_indices)}")
    
    def _calculate_scores(self, profile: str) -> np.ndarray:
        """
        Calcula el vector de scores para todas las recetas.
        
        Args:
            profile: Perfil nutricional del usuario.
            
        Returns:
            Array numpy con el score de cada receta.
        """
        scores = np.zeros(self.n)
        
        for i, recipe in enumerate(self.recipes):
            cost = recipe.calculate_cost()
            
            if profile == "budget":
                scores[i] = (10 / cost) * 5 if cost > 0 else 0
            elif profile == "fitness":
                scores[i] = (recipe.protein_pdv * 3) - (recipe.fat_pdv * 1.5) - (cost * 0.5)
            elif profile == "gourmet":
                scores[i] = recipe.rating * 20 + (5 if recipe.calories > 400 else 0)
            else:  # balanced
                scores[i] = recipe.protein_pdv - (recipe.fat_pdv * 0.5) - (cost * 2)
        
        return scores
    
    def _build_constraints(
        self,
        cal_max_daily: float,
        prot_min_daily: float
    ) -> list[LinearConstraint]:
        """
        Construye las restricciones lineales del problema.
        
        Args:
            cal_max_daily: Calorías máximas por día.
            prot_min_daily: Proteína mínima por día (% DV).
            
        Returns:
            Lista de objetos LinearConstraint para scipy.
        """
        constraints = []
        
        # --- Restricción 1: Calorías totales ≤ CalMax * 7 ---
        cal_coeffs = np.array([r.calories for r in self.recipes])
        constraints.append(LinearConstraint(
            A=cal_coeffs,
            lb=-np.inf,
            ub=cal_max_daily * 7
        ))
        
        # --- Restricción 2: Proteína total ≥ ProtMin * 7 ---
        prot_coeffs = np.array([r.protein_pdv for r in self.recipes])
        constraints.append(LinearConstraint(
            A=prot_coeffs,
            lb=prot_min_daily * 7,
            ub=np.inf
        ))
        
        # --- Restricción 3: Exactamente 7 desayunos ---
        breakfast_coeffs = np.zeros(self.n)
        breakfast_coeffs[self.breakfast_indices] = 1
        constraints.append(LinearConstraint(
            A=breakfast_coeffs,
            lb=7,
            ub=7
        ))
        
        # --- Restricción 4: Exactamente 14 comidas principales ---
        main_coeffs = np.zeros(self.n)
        main_coeffs[self.main_indices] = 1
        constraints.append(LinearConstraint(
            A=main_coeffs,
            lb=14,
            ub=14
        ))
        
        return constraints
    
    def optimize_menu(
        self,
        profile: str,
        cal_max_daily: float = 2000,
        prot_min_daily: float = 50
    ) -> tuple[list['Recipe'], dict]:
        """
        Encuentra el menú semanal óptimo usando MILP.
        
        Resuelve el problema de optimización:
            max  Σ x_i · score_i
            s.t. restricciones nutricionales y estructurales
        
        Args:
            profile: Perfil nutricional ('fitness', 'budget', 'gourmet', 'balanced').
            cal_max_daily: Calorías máximas permitidas por día.
            prot_min_daily: Proteína mínima requerida por día (% DV).
            
        Returns:
            Tupla (menu, stats) donde:
                - menu: Lista de 21 recetas ordenadas [D1_desayuno, D1_almuerzo, ...]
                - stats: Diccionario con estadísticas de la optimización
        """
        print(f"\n🧮 MILP Optimizer: Solving for profile '{profile}'...")
        print(f"   Constraints: cal ≤ {cal_max_daily}/day, prot ≥ {prot_min_daily}%/day")
        
        # 1. Calcular scores (función objetivo)
        scores = self._calculate_scores(profile)
        
        # scipy.milp MINIMIZA, así que negamos los scores para maximizar
        c = -scores
        
        # 2. Construir restricciones
        constraints = self._build_constraints(cal_max_daily, prot_min_daily)
        
        # 3. Variables binarias: x_i ∈ {0, 1}
        bounds = Bounds(lb=0, ub=1)
        integrality = np.ones(self.n)  # 1 = variable entera
        
        # 4. Resolver el problema MILP
        print("   ⏳ Running branch-and-bound algorithm...")
        result = milp(
            c=c,
            constraints=constraints,
            bounds=bounds,
            integrality=integrality,
            options={'disp': False, 'time_limit': 60}
        )
        
        if not result.success:
            print(f"   ⚠️ Optimization failed: {result.message}")
            print("   Falling back to relaxed constraints...")
            return self._fallback_optimize(profile)
        
        # 5. Extraer recetas seleccionadas
        selected_indices = np.where(result.x > 0.5)[0]
        
        # Separar en desayunos y principales
        selected_breakfasts = [i for i in selected_indices if i in self.breakfast_indices]
        selected_mains = [i for i in selected_indices if i in self.main_indices]
        
        # 6. Construir menú estructurado (7 días x 3 comidas)
        menu = []
        for day in range(7):
            if day < len(selected_breakfasts):
                menu.append(self.recipes[selected_breakfasts[day]])
            else:
                # Fallback: usar una comida principal como desayuno
                menu.append(self.recipes[selected_mains[0]])
            
            # Almuerzo y cena
            lunch_idx = day * 2
            dinner_idx = day * 2 + 1
            
            if lunch_idx < len(selected_mains):
                menu.append(self.recipes[selected_mains[lunch_idx]])
            if dinner_idx < len(selected_mains):
                menu.append(self.recipes[selected_mains[dinner_idx]])
        
        # 7. Calcular estadísticas
        total_cal = sum(r.calories for r in menu)
        total_prot = sum(r.protein_pdv for r in menu)
        total_score = -result.fun  # Negamos porque minimizamos -score
        
        stats = {
            'total_score': total_score,
            'total_calories': total_cal,
            'avg_daily_calories': total_cal / 7,
            'total_protein_pdv': total_prot,
            'avg_daily_protein_pdv': total_prot / 7,
            'optimization_status': result.message,
            'num_iterations': getattr(result, 'nit', 'N/A')
        }
        
        print(f"   ✅ Optimal solution found!")
        print(f"   📊 Total score: {total_score:.2f}")
        print(f"   🔥 Avg daily calories: {stats['avg_daily_calories']:.0f} kcal")
        print(f"   💪 Avg daily protein: {stats['avg_daily_protein_pdv']:.1f}% DV")
        
        return menu, stats
    
    def _fallback_optimize(self, profile: str) -> tuple[list['Recipe'], dict]:
        """
        Optimización de respaldo con restricciones relajadas.
        
        Se usa cuando el problema original es infactible.
        
        Args:
            profile: Perfil nutricional.
            
        Returns:
            Tupla (menu, stats) con solución subóptima.
        """
        print("   🔄 Using greedy fallback...")
        
        scores = self._calculate_scores(profile)
        
        # Ordenar por score descendente
        sorted_indices = np.argsort(-scores)
        
        # Seleccionar los mejores 7 desayunos y 14 principales
        selected_breakfasts = []
        selected_mains = []
        
        for idx in sorted_indices:
            if idx in self.breakfast_indices and len(selected_breakfasts) < 7:
                selected_breakfasts.append(idx)
            elif idx in self.main_indices and len(selected_mains) < 14:
                selected_mains.append(idx)
            
            if len(selected_breakfasts) == 7 and len(selected_mains) == 14:
                break
        
        # Construir menú
        menu = []
        for day in range(7):
            menu.append(self.recipes[selected_breakfasts[day]])
            menu.append(self.recipes[selected_mains[day * 2]])
            menu.append(self.recipes[selected_mains[day * 2 + 1]])
        
        total_cal = sum(r.calories for r in menu)
        total_prot = sum(r.protein_pdv for r in menu)
        
        stats = {
            'total_score': sum(scores[i] for i in selected_breakfasts + selected_mains),
            'total_calories': total_cal,
            'avg_daily_calories': total_cal / 7,
            'total_protein_pdv': total_prot,
            'avg_daily_protein_pdv': total_prot / 7,
            'optimization_status': 'Fallback (greedy)',
            'num_iterations': 'N/A'
        }
        
        return menu, stats
    
    def compare_with_heuristic(
        self,
        heuristic_menu: list['Recipe'],
        optimal_menu: list['Recipe'],
        profile: str
    ) -> dict:
        """
        Compara el menú heurístico con el óptimo.
        
        Útil para demostrar la mejora del algoritmo MILP.
        
        Args:
            heuristic_menu: Menú generado por el Optimizer básico.
            optimal_menu: Menú generado por MILP.
            profile: Perfil nutricional.
            
        Returns:
            Diccionario con métricas de comparación.
        """
        scores = self._calculate_scores(profile)
        
        # Calcular score total de cada menú
        heuristic_score = sum(
            scores[self.recipes.index(r)] 
            for r in heuristic_menu 
            if r in self.recipes
        )
        optimal_score = sum(
            scores[self.recipes.index(r)] 
            for r in optimal_menu 
            if r in self.recipes
        )
        
        improvement = ((optimal_score - heuristic_score) / abs(heuristic_score)) * 100 if heuristic_score != 0 else 0
        
        return {
            'heuristic_score': heuristic_score,
            'optimal_score': optimal_score,
            'improvement_percent': improvement,
            'heuristic_calories': sum(r.calories for r in heuristic_menu),
            'optimal_calories': sum(r.calories for r in optimal_menu)
        }
