import pandas as pd
import os
import time
from src import data_loader, optimizer, pantry
from src.modelos import Recipe


# --- 1. CONFIG & UTILS ---

def show_disclaimer():
    print("\n" + "-" * 60)
    print(" ⚠️  IMPORTANT DATA DISCLAIMER")
    print("-" * 60)
    print(" This app uses a public dataset (Food.com).")
    print(" Recipes have been filtered to remove obvious errors,")
    print(" but please review ingredients before cooking.")
    print("-" * 60 + "\n")


def filter_recipes_by_goal(df, goal):
    print("⚙️  Applying nutritional filters...")

    # Define limits based on goal
    if goal == "1":  # Weight Loss
        min_cal, max_cal, min_prot = 200, 500, 15
    elif goal == "2":  # Muscle Gain
        min_cal, max_cal, min_prot = 400, 1000, 25
    elif goal == "3":  # Balanced
        min_cal, max_cal, min_prot = 300, 800, 10
    else:  # Gourmet
        min_cal, max_cal, min_prot = 0, 1500, 0

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

def show_detail_and_actions(recipe, weekly_menu, idx, my_optimizer):
    """
    Shows detail for ONE recipe and allows replacing it.
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


def manage_interactive_menu(weekly_menu, my_optimizer, mode="weekly", day_idx=None):
    """
    Main interaction loop.
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

        print("🎯 CHOOSE YOUR GOAL:")
        print("   1. Weight Loss")
        print("   2. Muscle Gain")
        print("   3. Balanced Diet")
        print("   4. Gourmet (Flavor focus)")

        choice = input("\n👉 Your choice (1-4): ")
        candidates_df = filter_recipes_by_goal(df, choice)

        if len(candidates_df) > 50:
            print("📦 Converting data to objects...")
            recipe_objects = [Recipe(row) for index, row in candidates_df.iterrows()]
            my_optimizer = optimizer.Optimizer(recipe_objects)

            profile_map = {"1": "fitness", "2": "fitness", "3": "balanced", "4": "gourmet"}
            selected_profile = profile_map.get(choice, "balanced")

            # Generate initial menu
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
                    pantry.print_shopping_list(weekly_menu)
                    input("\nPress Enter to continue...")

                elif action == "q":
                    print("👋 See you soon! Eat healthy.")
                    break

                else:
                    print("⚠️ Invalid option.")
        else:
            print("⚠️ Not enough recipes found for this profile.")