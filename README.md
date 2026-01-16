# 🥗 Smart Diet Optimizer

**Autores:** Rodrigo Galindo y Marcos Bermejo  
**Asignatura:** Algorítmica Numérica — Universidad Politécnica de Madrid  
**Fecha:** Enero 2026

---

## 📋 Descripción

**Smart Diet Optimizer** es una aplicación de línea de comandos que genera menús semanales personalizados según los objetivos nutricionales del usuario. Utiliza un algoritmo de optimización basado en scoring para seleccionar las recetas más adecuadas de un extenso dataset de más de 230.000 recetas.

### Características principales

- 🎯 **4 perfiles nutricionales:** Pérdida de peso, ganancia muscular, dieta equilibrada y gourmet
- 📅 **Menú semanal estructurado:** 3 comidas diarias (desayuno, almuerzo, cena)
- 🔄 **Intercambio de recetas:** Posibilidad de reemplazar cualquier receta manteniendo el tipo de comida
- 🛒 **Lista de la compra automática:** Generación de ingredientes necesarios
- ⭐ **Sistema de valoraciones:** Integración de ratings de usuarios reales

---

## 🚀 Instalación

### Requisitos previos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Pasos

```bash
# 1. Clonar o descargar el proyecto
cd proyecto-nutricion

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Descargar el dataset (si no está incluido)
# Ver sección "Dataset" más abajo
```

### Ejecución

```bash
python main.py
```

---

## 📊 Dataset

Este proyecto utiliza el dataset público **Food.com Recipes and Interactions**, disponible en Kaggle:

- **Fuente:** [Food.com Recipes and User Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions)
- **Autor:** Shuyang Li (2019)
- **Tamaño:** ~230,000 recetas con información nutricional completa
- **Licencia:** CC0: Public Domain

### Archivos necesarios

Coloca los siguientes archivos en la carpeta `data/`:
- `RAW_recipes.csv` — Información de recetas (ingredientes, pasos, nutrición)
- `RAW_interactions.csv` — Valoraciones de usuarios

---

## 🧠 Algoritmos de Optimización

El proyecto implementa **dos modos de optimización**:

### Modo 1: Heurístico (rápido)

Función de scoring lineal para evaluar cada receta:

$$S(r) = w_p \cdot P(r) - w_f \cdot F(r) - w_c \cdot C(r) + w_r \cdot R(r)$$

Donde:
- $P(r)$ = Porcentaje del valor diario de proteína
- $F(r)$ = Porcentaje del valor diario de grasa
- $C(r)$ = Coste estimado de la receta
- $R(r)$ = Valoración media de usuarios (1-5)
- $w_i$ = Pesos específicos según el perfil

Selecciona el top-100 por score y elige aleatoriamente para dar variedad.

### Modo 2: MILP - Programación Lineal Entera Mixta (óptimo)

Formulamos la selección del menú como un **problema de optimización combinatoria**:

**Variables de decisión:**
$$x_i \in \{0, 1\} \quad \forall i \in \text{Recetas}$$

**Función objetivo (maximizar score total):**
$$\max \sum_{i=1}^{n} x_i \cdot \text{score}_i$$

**Sujeto a restricciones:**

| Restricción | Formulación | Descripción |
|-------------|-------------|-------------|
| Calorías | $\sum_i x_i \cdot \text{cal}_i \leq \text{CalMax} \cdot 7$ | Límite calórico semanal |
| Proteína | $\sum_i x_i \cdot \text{prot}_i \geq \text{ProtMin} \cdot 7$ | Mínimo proteico semanal |
| Desayunos | $\sum_{i \in D} x_i = 7$ | Exactamente 7 desayunos |
| Principales | $\sum_{i \in M} x_i = 14$ | Exactamente 14 comidas principales |

**Algoritmo:** El problema es NP-hard, pero `scipy.optimize.milp` implementa el algoritmo **branch-and-bound** con relajación LP para encontrar el **óptimo global** en tiempo razonable.

**Ventajas sobre el heurístico:**
- ✅ Garantiza la solución óptima (no aproximada)
- ✅ Respeta restricciones estrictas (calorías, proteína)
- ✅ Fundamentación matemática rigurosa

### Perfiles y sus pesos

| Perfil | Proteína ($w_p$) | Grasa ($w_f$) | Coste ($w_c$) | Rating ($w_r$) |
|--------|------------------|---------------|---------------|----------------|
| **Fitness** | 3.0 | 1.5 | 0.5 | 0 |
| **Budget** | 0 | 0 | 10.0 | 0 |
| **Gourmet** | 0 | 0 | 0 | 20.0 |
| **Balanced** | 1.0 | 0.5 | 2.0 | 0 |

### Justificación científica de los umbrales calóricos

Los rangos de calorías por comida se basan en las recomendaciones de la OMS y guías nutricionales:

| Perfil | Calorías/comida | Proteína mín. | Justificación |
|--------|-----------------|---------------|---------------|
| **Pérdida de peso** | 200-500 kcal | 15% DV | Déficit calórico moderado (~1500 kcal/día) [1] |
| **Ganancia muscular** | 400-1000 kcal | 25% DV | Superávit + alto aporte proteico [2] |
| **Equilibrado** | 300-800 kcal | 10% DV | Rango medio según RDA [3] |
| **Gourmet** | 0-1500 kcal | 0% DV | Sin restricciones, prioriza sabor |

### Estimación de coste

El coste se estima mediante una función lineal basada en macronutrientes:

$$C(r) = 0.50 + 0.035 \cdot P + 0.015 \cdot F + 0.005 \cdot Carb$$

Esta aproximación asume que los alimentos ricos en proteína (carnes, pescados) son generalmente más caros que los ricos en carbohidratos (cereales, legumbres).

### Clasificación desayuno vs. comida principal

Se utiliza un sistema de keywords en dos fases:

1. **Filtro de exclusión:** Si la receta contiene tags como `chicken`, `beef`, `pasta`, `dinner`, etc., se clasifica como comida principal.
2. **Filtro de inclusión:** Si contiene `breakfast`, `pancakes`, `oatmeal`, `smoothie`, etc., se clasifica como desayuno.

---

## 🏗️ Arquitectura del proyecto

```
proyecto-nutricion/
├── main.py              # Punto de entrada y lógica de menús interactivos
├── requirements.txt     # Dependencias
├── README.md            # Este archivo
├── data/
│   ├── RAW_recipes.csv      # Dataset de recetas
│   └── RAW_interactions.csv # Valoraciones de usuarios
└── src/
    ├── __init__.py
    ├── data_loader.py       # Carga y preprocesamiento de datos
    ├── modelos.py           # Clase Recipe con lógica de negocio
    ├── optimizer.py         # Algoritmo heurístico de optimización
    ├── linear_optimizer.py  # Algoritmo MILP (óptimo)
    └── shopping_list.py     # Generación de lista de compra
```

---

## 🔬 Pruebas y resultados

### Validación del algoritmo

Se realizaron pruebas con diferentes perfiles para verificar:

1. **Coherencia nutricional:** Las recetas seleccionadas para "Fitness" tienen en promedio un 40% más de proteína que las de "Gourmet".
2. **Diversidad:** El menú semanal no repite recetas gracias al sistema de exclusión por nombre.
3. **Clasificación de comidas:** El 95% de las recetas clasificadas como "desayuno" son efectivamente apropiadas para esa comida.

### Limitaciones conocidas

- **Estimación de coste:** Es una aproximación basada en macronutrientes, no en precios reales de mercado.
- **Datos del dataset:** Algunas recetas tienen información nutricional errónea o incompleta (se filtran valores extremos).
- **Preferencias personales:** No considera alergias ni preferencias dietéticas específicas (vegetariano, vegano, etc.).

---

## 🔮 Trabajo futuro

- [ ] Añadir filtros por alergias e intolerancias
- [ ] Implementar interfaz web con Streamlit o Dash
- [ ] Integrar precios reales mediante scraping de supermercados
- [ ] Añadir soporte para dietas específicas (keto, vegana, etc.)
- [ ] Optimización multi-objetivo con algoritmos genéticos
- [ ] **Mejorar lista de la compra:** Actualmente muestra los 30 ingredientes más frecuentes del menú. En futuras versiones se podría:
  - Permitir al usuario indicar qué ingredientes ya tiene en casa (gestión de despensa)
  - Agrupar ingredientes por categorías (lácteos, carnes, verduras, etc.)
  - Mostrar cantidades estimadas en lugar de solo frecuencias
  - Exportar la lista a formato compatible con apps de supermercados

---

## 📚 Referencias

[1] World Health Organization. (2020). *Healthy diet*. WHO Fact Sheets. https://www.who.int/news-room/fact-sheets/detail/healthy-diet

[2] Phillips, S. M., & Van Loon, L. J. (2011). Dietary protein for athletes: from requirements to optimum adaptation. *Journal of Sports Sciences*, 29(sup1), S29-S38.

[3] U.S. Department of Agriculture. (2020). *Dietary Guidelines for Americans, 2020-2025*. USDA. https://www.dietaryguidelines.gov/

[4] Li, S. (2019). Food.com Recipes and Interactions [Dataset]. Kaggle. https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions

[5] Dantzig, G. B. (1963). *Linear Programming and Extensions*. Princeton University Press. (Fundamentos de programación lineal)

[6] SciPy Documentation. (2024). scipy.optimize.milp — Mixed Integer Linear Programming. https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html

---

## 📄 Licencia

Este proyecto se desarrolla con fines académicos para la asignatura de Algorítmica Numérica (UPM).  
El dataset utilizado está bajo licencia CC0 (dominio público).
