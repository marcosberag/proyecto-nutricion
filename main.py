"""
Smart Diet Optimizer - Aplicación principal.

Generador de menús semanales personalizados según objetivos nutricionales.
Utiliza el dataset de Food.com con ~230k recetas.

Autores: Rodrigo Galindo y Marcos Bermejo
Asignatura: Algorítmica Numérica - UPM

Usage:
    python main.py
"""

import pandas as pd
import os
import time
from src import data_loader, optimizer, shopping_list
from src.linear_optimizer import LinearOptimizer
from src.modelos import Recipe


# --- 1. CONFIG & UTILS ---

def show_disclaimer() -> None:
    """Muestra el aviso legal sobre los datos del dataset."""
    print("\n" + "-" * 60)
    print(" ⚠️  IMPORTANT DATA DISCLAIMER")
    print("-" * 60)
    print(" This app uses a public dataset (Food.com).")
    print(" Recipes have been filtered to remove obvious errors,")
    print(" but please review ingredients before cooking.")
    print("-" * 60 + "\n")


def filter_recipes_by_goal(df: pd.DataFrame, goal: str) -> pd.DataFrame:
    """
    Filtra recetas según el perfil nutricional del usuario.

    Args:
        df: DataFrame con las recetas procesadas.
        goal: Código del perfil:
            '1' = Fitness (300-900 kcal, 20% proteína mín)
            '2' = Budget (200-700 kcal, 10% proteína mín)
            '3' = Gourmet (sin restricciones)
            '4' = Balanced (300-800 kcal, 10% proteína mín)

    Returns:
        DataFrame filtrado con recetas que cumplen los criterios.

    Notes:
        Si hay menos de 50 recetas, expande los límites automáticamente.
        Umbrales basados en guías dietéticas generales.
    """
    print("⚙️  Applying nutritional filters...")

    # Define limits based on goal
    if goal == "1":  # Fitness
        min_cal, max_cal, min_prot = 300, 900, 20
    elif goal == "2":  # Budget
        min_cal, max_cal, min_prot = 200, 700, 10
    elif goal == "3":  # Gourmet
        min_cal, max_cal, min_prot = 0, 1500, 0
    else:  # Balanced
        min_cal, max_cal, min_prot = 300, 800, 10

    filtered_df = df[
        (df['calories'] >= min_cal) &
        (df['calories'] <= max_cal) &
        (df['protein'] >= min_prot)
        ]
    filtered_df = filtered_df.drop_duplicates(subset=['name'])

    # Fallback logic
    if len(filtered_df) < 50:
        print(f"⚠️ Few recipes found ({len(filtered_df)}). Expanding search...")
        filtered_df = df[
            (df['calories'] >= min_cal) &
            (df['calories'] <= max_cal * 1.5) &
            (df['protein'] >= min_prot * 0.8)
            ]
        filtered_df = filtered_df.drop_duplicates(subset=['name'])

    print(f"✅ Final candidates: {len(filtered_df)}")
    return filtered_df


# --- 2. INTERACTIVE MENU LOGIC ---

def show_detail_and_actions(
    recipe: Recipe,
    weekly_menu: list[Recipe],
    idx: int,
    my_optimizer: optimizer.Optimizer
) -> bool:
    """
    Muestra los detalles de una receta y permite reemplazarla.
    
    Args:
        recipe: Receta a mostrar.
        weekly_menu: Menú semanal completo.
        idx: Índice de la receta en el menú.
        my_optimizer: Instancia del optimizador para buscar sustitutos.
        
    Returns:
        False siempre (indica que no se salió del menú principal).
    """
    while True:
        recipe.show_full_details()
        print("\nACTIONS:")
        print(" [Enter] Go back")
        print(" [C]     🔄 Change this recipe")

        action = input("👉 Choose: ").strip().upper()

        if action == "":
            return False  # No change happened

        elif action == "C":
            print("⏳ Looking for substitute...")
            new_recipe = my_optimizer.replace_recipe(recipe, weekly_menu)
            if new_recipe:
                weekly_menu[idx] = new_recipe
                print(f"✅ CHANGED! New recipe: {new_recipe.name}")
                recipe = new_recipe  # Update local var to show the new one
            else:
                print("⚠️ No more unique recipes of this type available.")
                time.sleep(2)
        else:
            print("⚠️ Invalid option.")


def manage_interactive_menu(
    weekly_menu: list[Recipe],
    my_optimizer: optimizer.Optimizer,
    mode: str = "weekly",
    day_idx: int | None = None
) -> str | None:
    """
    Bucle principal de interacción con el menú.
    
    Args:
        weekly_menu: Lista de 21 recetas (7 días x 3 comidas).
        my_optimizer: Instancia del optimizador.
        mode: 'weekly' para vista semanal, 'daily' para vista diaria.
        day_idx: Índice del día (0-6) si mode='daily'.
        
    Returns:
        'REGENERATE' si el usuario quiere regenerar el menú,
        None en caso contrario.
        
    Commands:
        - [Número]: Ver detalles de receta
        - [C + Número]: Cambiar receta
        - [R]: Regenerar semana completa (solo modo weekly)
        - [Enter]: Volver al menú anterior
    """
    week_days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

    while True:
        # --- A. SHOW LIST ---
        print("\n" + "=" * 60)
        if mode == "weekly":
            print("📅 WEEKLY MENU OVERVIEW")
            indices_range = range(len(weekly_menu))
        else:
            day_name = week_days[day_idx]
            print(f"📆 DAILY MENU: {day_name}")
            start = day_idx * 3
            indices_range = range(start, start + 3)

        print("-" * 60)

        for i in indices_range:
            recipe = weekly_menu[i]
            # Calculate type based on index
            mod = i % 3
            icon = "☕" if mod == 0 else "🍽️ " if mod == 1 else "🌙"
            label = "Breakfast" if mod == 0 else "Lunch    " if mod == 1 else "Dinner   "

            # Truncate name for display
            display_name = (recipe.name[:35] + '..') if len(recipe.name) > 35 else recipe.name

            print(
                f" [{i + 1:2d}] {icon} {label}: {display_name:<38} ({recipe.calories:.0f} kcal) {'★' * int(recipe.rating)}")

        print("=" * 60)
        print("COMMANDS:")
        print(" • Type [Number] to see details & reviews.")
        print(" • Type [C + Number] to change a recipe (e.g., C5).")
        if mode == "weekly":
            print(" • Type [R] to regenerate (shuffle) the whole week.")
        print(" • Press [Enter] to go back.")

        # --- B. CAPTURE INPUT ---
        user_input = input("\n👉 Command: ").strip().upper()

        if user_input == "":
            break  # Exit loop

        # OPTION: REGENERATE WEEK (Only in weekly mode)
        if mode == "weekly" and user_input == "R":
            confirm = input("⚠️ Are you sure you want to shuffle the ENTIRE week? (y/n): ")
            if confirm.lower() == 'y':
                return "REGENERATE"  # Signal to main

        # OPTION: CHANGE (C + NUM)
        elif user_input.startswith("C"):
            try:
                user_idx = int(user_input[1:])
                real_idx = user_idx - 1

                if real_idx in indices_range:
                    old_recipe = weekly_menu[real_idx]
                    new_recipe = my_optimizer.replace_recipe(old_recipe, weekly_menu)
                    if new_recipe:
                        weekly_menu[real_idx] = new_recipe
                        print(f"✅ Done! {old_recipe.name} -> {new_recipe.name}")
                        time.sleep(1)
                    else:
                        print("⚠️ No substitutes found.")
                else:
                    print("⚠️ Number not currently visible.")
            except ValueError:
                print("⚠️ Invalid format. Use C + Number (e.g., C1)")

        # OPTION: SEE DETAILS (NUM)
        elif user_input.isdigit():
            user_idx = int(user_input)
            real_idx = user_idx - 1

            if 0 <= real_idx < len(weekly_menu):
                recipe = weekly_menu[real_idx]
                show_detail_and_actions(recipe, weekly_menu, real_idx, my_optimizer)
            else:
                print("⚠️ Number out of range.")

        else:
            print("⚠️ Unknown command.")


# --- 3. MAIN ENTRY POINT ---

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    recipes_path = os.path.join(base_dir, 'data', 'RAW_recipes.csv')
    interactions_path = os.path.join(base_dir, 'data', 'RAW_interactions.csv')

    print("⏳ Starting system...")
    df = data_loader.load_data(recipes_path, interactions_path)

    if df is not None:
        df = data_loader.process_data(df)
        print("\n--- 🥗 SMART DIET OPTIMIZER ---")
        show_disclaimer()

        print("🎯 CHOOSE YOUR PROFILE:")
        print("   1. Fitness")
        print("   2. Budget")
        print("   3. Gourmet")
        print("   4. Balanced")

        choice = input("\n👉 Your choice (1-4): ")
        candidates_df = filter_recipes_by_goal(df, choice)

        if len(candidates_df) > 50:
            print("📦 Converting data to objects...")
            recipe_objects = [Recipe(row) for index, row in candidates_df.iterrows()]

            profile_map = {"1": "fitness", "2": "budget", "3": "gourmet", "4": "balanced"}
            selected_profile = profile_map.get(choice, "balanced")

            # Preguntar modo de optimización
            print("\n⚙️  OPTIMIZATION MODE:")
            print("   1. Heuristic (fast, good quality)")
            print("   2. MILP - Linear Programming (slower, optimal solution)")
            opt_mode = input("\n👉 Mode (1-2): ").strip()

            # Configurar límites calóricos según perfil
            cal_limits = {
                "fitness": (2000, 80),    # cal_max_daily, prot_min_daily
                "budget": (1800, 50),
                "balanced": (2000, 50),
                "gourmet": (2500, 30)
            }
            cal_max, prot_min = cal_limits.get(selected_profile, (2000, 50))

            if opt_mode == "2":
                # Usar optimizador lineal (MILP)
                print("\n🧠 Initializing Linear Programming optimizer...")
                linear_opt = LinearOptimizer(recipe_objects)
                weekly_menu, stats = linear_opt.optimize_menu(
                    profile=selected_profile,
                    cal_max_daily=cal_max,
                    prot_min_daily=prot_min
                )
                my_optimizer = optimizer.Optimizer(recipe_objects)  # Para reemplazos
                
                # Mostrar comparación con heurístico
                print("\n📊 OPTIMIZATION RESULTS:")
                print(f"   - Optimization status: {stats['optimization_status']}")
                print(f"   - Total score: {stats['total_score']:.2f}")
                print(f"   - Avg daily calories: {stats['avg_daily_calories']:.0f} kcal")
                print(f"   - Avg daily protein: {stats['avg_daily_protein_pdv']:.1f}% DV")
            else:
                # Usar optimizador heurístico (original)
                my_optimizer = optimizer.Optimizer(recipe_objects)
                weekly_menu = my_optimizer.generate_structured_menu(selected_profile)

            while True:
                # Main Menu with Sentence Case
                print("\n" + "=" * 50)
                print(f"   📱 Main menu ({selected_profile.capitalize()})")
                print("=" * 50)
                print("1. View weekly menu")
                print("2. Daily menus")
                print("3. Generate shopping list")
                print("q. Exit")

                action = input("\n👉 Action: ").lower().strip()

                if action == "1":
                    result = manage_interactive_menu(weekly_menu, my_optimizer, mode="weekly")
                    if result == "REGENERATE":
                        print("🎲 Reshuffling universe...")
                        weekly_menu = my_optimizer.generate_structured_menu(selected_profile)

                elif action == "2":
                    print("\nSelect day (1-7):")
                    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    for i, d in enumerate(days): print(f" {i + 1}. {d}")
                    try:
                        idx = int(input("Day: ")) - 1
                        if 0 <= idx < 7:
                            manage_interactive_menu(weekly_menu, my_optimizer, mode="daily", day_idx=idx)
                        else:
                            print("⚠️ Invalid day.")
                    except ValueError:
                        print("⚠️ Enter a number.")

                elif action == "3":
                    shopping_list.print_shopping_list(weekly_menu)
                    input("\nPress Enter to continue...")

                elif action == "q":
                    print("👋 See you soon! Eat healthy.")
                    break

                else:
                    print("⚠️ Invalid option.")
        else:
            print("⚠️ Not enough recipes found for this profile.")