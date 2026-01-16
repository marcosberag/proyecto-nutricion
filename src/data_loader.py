"""Módulo de carga y preprocesamiento de datos de recetas.

Este módulo se encarga de cargar los datasets de Food.com,
procesar las columnas y limpiar datos erróneos.
"""

import pandas as pd
import ast


def process_data(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """
    Procesa el DataFrame de recetas: convierte strings a listas y limpia datos.
    
    Args:
        df: DataFrame crudo con las recetas cargadas.
        
    Returns:
        DataFrame procesado y limpio, o None si la entrada es None.
        
    Notes:
        - Convierte columnas 'nutrition', 'ingredients', 'steps', 'tags' de str a list
        - Extrae columnas auxiliares 'calories' y 'protein'
        - Elimina recetas con calorías < 10 o > 2500 (datos corruptos)
    """
    if df is None: return None

    # 1. Format conversion (Strings to Lists)
    list_columns = ['nutrition', 'ingredients', 'steps', 'tags']

    for col in list_columns:
        df[col] = df[col].apply(ast.literal_eval)

    # 2. Extract auxiliary columns
    df['calories'] = df['nutrition'].apply(lambda x: x[0])
    df['protein'] = df['nutrition'].apply(lambda x: x[4])

    # 3. Data Cleaning (Sanity Check)
    # Remove recipes with < 10 kcal or > 2500 kcal (errors)
    clean_df = df[
        (df['calories'] > 10) &
        (df['calories'] < 2500)
        ]

    removed = len(df) - len(clean_df)
    if removed > 0:
        print(f"🧹 Data loader: Removed {removed} recipes with extreme/corrupt data.")

    return clean_df


def load_data(
    recipes_path: str,
    interactions_path: str,
    row_restriction: int | None = None
) -> pd.DataFrame | None:
    """
    Carga y combina los datasets de recetas e interacciones.
    
    Args:
        recipes_path: Ruta al archivo CSV de recetas (RAW_recipes.csv).
        interactions_path: Ruta al archivo CSV de interacciones (RAW_interactions.csv).
        row_restriction: Número máximo de filas a cargar (None = todas).
        
    Returns:
        DataFrame combinado con recetas y sus valoraciones medias,
        o None si ocurre un error de carga.
        
    Notes:
        - Calcula la media de ratings por receta
        - Recetas sin valoraciones reciben avg_rating = 0
    """
    print(f"Loading data...")
    try:
        recipes = pd.read_csv(recipes_path, nrows=row_restriction)
        # Load only necessary columns to save RAM
        interactions = pd.read_csv(interactions_path, usecols=['recipe_id', 'rating'])

        # Calculate mean rating
        avg_ratings = interactions.groupby('recipe_id')['rating'].mean().reset_index()
        avg_ratings.rename(columns={'rating': 'avg_rating'}, inplace=True)

        # Merge tables
        final_df = pd.merge(recipes, avg_ratings, left_on='id', right_on='recipe_id', how='left')
        final_df['avg_rating'] = final_df['avg_rating'].fillna(0)

        return final_df

    except Exception as e:
        print(f'❌ Critical error in data_loader: {e}')
        return None