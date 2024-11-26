import streamlit as st
import pandas as pd

# Load the dataset
df = pd.read_csv('./nutrients_csvfile.py')

# Convert relevant columns to numeric, handling non-numeric values
numeric_columns = ['Calories', 'Protein', 'Carbs', 'Fat']
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with missing values in these columns after conversion
df = df.dropna(subset=numeric_columns)

# Title and description
st.title("Personalized Nutrition Planner")
st.write("Calculate your daily calorie and macronutrient needs, and get meal suggestions.")

# User Inputs
st.sidebar.header("Enter Your Details")
height = st.sidebar.number_input("Height (cm):", min_value=100, max_value=250, value=170)
weight = st.sidebar.number_input("Weight (kg):", min_value=30, max_value=200, value=70)
protein_goal = st.sidebar.number_input("Protein Goal (g):", min_value=20, max_value=300, value=100)
activity_level = st.sidebar.selectbox("Activity Level", ["Sedentary", "Lightly active", "Moderately active", "Very active"])
goal = st.sidebar.radio("Goal", ["Cut", "Bulk"])
age = st.sidebar.number_input("Age:", min_value=15, max_value=100, value=25)

# Calorie Calculation based on user data and activity level
def calculate_calories(weight, height, age, activity_level, goal):
    # Basic BMR calculation (Harris-Benedict equation)
    bmr = 10 * weight + 6.25 * height - 5 * age + 5  # Assuming male; modify if needed

    # Adjust BMR based on activity level
    if activity_level == "Sedentary":
        calories = bmr * 1.2
    elif activity_level == "Lightly active":
        calories = bmr * 1.375
    elif activity_level == "Moderately active":
        calories = bmr * 1.55
    elif activity_level == "Very active":
        calories = bmr * 1.725

    # Adjust for goal (cut or bulk)
    if goal == "Cut":
        calories *= 0.85  # Reduce by 15% for cutting
    elif goal == "Bulk":
        calories *= 1.15  # Increase by 15% for bulking

    return round(calories)

# Calculate macronutrient split
def calculate_macros(calories, protein_goal):
    protein_calories = protein_goal * 4
    remaining_calories = calories - protein_calories
    fat_calories = remaining_calories * 0.3  # 30% of remaining for fats
    carb_calories = remaining_calories - fat_calories  # Remainder for carbs

    carbs = round(carb_calories / 4)  # 1g carb = 4 calories
    fats = round(fat_calories / 9)    # 1g fat = 9 calories
    protein = protein_goal            # Set by user

    return carbs, fats, protein

# Get suggested meals
def get_meal_suggestions(df, meal_calories, protein_per_meal):
    def get_meals_for_time(meal_time, target_calories, target_protein, num_options=1):
        # Filter for specific meal time
        meal_df = df[df['Meal_time'] == meal_time]
        
        # Try to find meals within desired calorie and protein range
        suggested_meals = meal_df[
            (meal_df['Calories'] >= target_calories * 0.8) & 
            (meal_df['Calories'] <= target_calories * 1.2) &
            (meal_df['Protein'] >= target_protein * 0.5)
        ]
        
        # If no meals found, try with broader calorie range
        if len(suggested_meals) == 0:
            suggested_meals = meal_df[
                (meal_df['Calories'] >= target_calories * 0.6) & 
                (meal_df['Calories'] <= target_calories * 1.4)
            ]
        
        # If still no meals found, just get any meal for that time
        if len(suggested_meals) == 0:
            suggested_meals = meal_df
        
        # Return multiple random meals if available
        if len(suggested_meals) > 0:
            num_options = min(num_options, len(suggested_meals))
            meals = suggested_meals.sample(num_options)
            return [
                {
                    'Name': meal['Food'],
                    'Calories': meal['Calories'],
                    'Protein': meal['Protein'],
                    'Carbs': meal['Carbs'],
                    'Fat': meal['Fat'],
                    'Measure': meal['Measure']
                } for _, meal in meals.iterrows()
            ]
        return [f"No suitable {meal_time} options found"]

    breakfast = get_meals_for_time('Breakfast', meal_calories, protein_per_meal, num_options=2)
    lunch = get_meals_for_time('Lunch', meal_calories, protein_per_meal, num_options=3)
    dinner = get_meals_for_time('Dinner', meal_calories, protein_per_meal, num_options=3)
    
    return breakfast, lunch, dinner

# Calculate total calories and macros
total_calories = calculate_calories(weight, height, age, activity_level, goal)
carbs, fats, protein = calculate_macros(total_calories, protein_goal)

# Display calorie and macronutrient information
st.write("### Daily Caloric Needs and Macronutrients")
st.write(f"**Calories:** {total_calories} kcal")
st.write(f"**Carbohydrates:** {carbs}g")
st.write(f"**Fats:** {fats}g")
st.write(f"**Protein:** {protein}g")

# Suggest meal options
st.write("### Suggested Meals")

# Divide calories for each meal
meal_calories = total_calories / 3
protein_per_meal = protein_goal / 3

breakfast, lunch, dinner = get_meal_suggestions(df, meal_calories, protein_per_meal)

# Helper function to convert meal list to dataframe
def meals_to_df(meals):
    if isinstance(meals[0], dict):
        return pd.DataFrame([
            {
                'Option': f'Option {i+1}',
                'Food': meal['Name'],
                'Portion': meal['Measure'],
                'Calories (kcal)': meal['Calories'],
                'Protein (g)': meal['Protein'],
                'Carbs (g)': meal['Carbs'],
                'Fat (g)': meal['Fat']
            } for i, meal in enumerate(meals)
        ])
    else:
        return pd.DataFrame({'Message': meals})

st.write("**Breakfast Options:")
breakfast_df = meals_to_df(breakfast)
st.dataframe(breakfast_df, hide_index=True)

st.write("\n**Lunch Options:")
lunch_df = meals_to_df(lunch)
st.dataframe(lunch_df, hide_index=True)

st.write("\n**Dinner Options:")
dinner_df = meals_to_df(dinner)
st.dataframe(dinner_df, hide_index=True)
