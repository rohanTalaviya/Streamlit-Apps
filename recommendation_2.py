import streamlit as st
from datetime import date, datetime
from math import ceil
import json
import math
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
import random
import json

# MongoDB connection details
MONGO_URI = "mongodb://Kishan:KishankFitshield@ec2-13-233-104-209.ap-south-1.compute.amazonaws.com:27017/?authMechanism=SCRAM-SHA-256&authSource=Fitshield"
client = MongoClient(MONGO_URI)
db = client["Fitshield"]


RestaurantMenuData = db["RestaurantMenuData"]


menu_data = RestaurantMenuData.find_one({"_id": "restro_ANAVRIN_395010_40269a87-3a94-4ea3-975d-887e680aac12"})

col1, col2, col3, col4 = st.columns(4)  # Creates four smaller columns

with col1:
    protien_live_goal_value = st.number_input("Proteins", value=50, step=1, key="protein_input")

with col2:
    cabs_live_goal_value = st.number_input("Carbs", value=20, step=1, key="carbs_input")

with col3:
    fats_live_goal_value = st.number_input("Fats", value=20, step=1, key="fats_input")

with col4:
    fiber_live_goal_value = st.number_input("Fibers", value=10, step=1, key="fiber_input")

col11, col21, col31, col41 = st.columns(4)  # Creates four smaller columns

with col11:
    defult_protien_factor = st.number_input("Proteins Factor", value=5, step=1, key="protein_factor")

with col21:
    defult_carbs_factor = st.number_input("Carbs Factor", value=3, step=1, key="carbs_factor")

with col31:
    defult_fats_factor = st.number_input("Fats Factor", value=2, step=1, key="fats_factor")

with col41:
    defult_fiber_factor = st.number_input("Fibers Factor", value=1, step=1, key="fiber_factor")

col111, col211, col311 = st.columns(3)  # Creates four smaller columns

with col111:
    density_factor = st.number_input("Density Factor", value=4, step=1, key="density_factor")

with col211:
    satiety_factor = st.number_input("Satiety Factor", value=2, step=1, key="satiety_factor")

with col311:
    euclidean_factor = st.number_input("Euclidean Factor", value=4, step=1, key="euclidean_factor")



def extract_nutrients(dish):
     macro_nutrients = dish["dish_variants"]["normal"]["full"]["calculate_nutrients"]["macro_nutrients"]
     dish_macro_nutrients_values = {n["name"]: n["value"] for n in macro_nutrients}
     return dish_macro_nutrients_values

def calculate_score(dish, hunger_level, user_live_goal, live_goal_energy, percentage_difference):

    protien_dish_percentage = float(dish["distributed_percentage"].get("proteins", 0).replace("%", ""))
    cabs_dish_percentage = float(dish["distributed_percentage"].get("carbs", 0).replace("%", ""))
    fats_dish_percentage = float(dish["distributed_percentage"].get("fats", 0).replace("%", ""))
    fiber_dish_percentage = float(dish["distributed_percentage"].get("fibers", 0).replace("%", ""))


    high_satiety_factor = 0.5
    low_satiety_factor = -0.3
    medium_satiety_factor = 0

    epsilon = 1e-6  # Small value to avoid division by zero
    live_goal_energy = live_goal_energy if live_goal_energy != 0 else epsilon

    macro_nutrients = dish["dish_variants"]["normal"]["full"]["calculate_nutrients"]["macro_nutrients"]
    dish_energy = next((item["value"] for item in macro_nutrients if item["name"] == "energy"), 0)
    dish_protein = next((item["value"] for item in macro_nutrients if item["name"] == "proteins"), 0)
    dish_carbs = next((item["value"] for item in macro_nutrients if item["name"] == "carbs"), 0)
    dish_fats = next((item["value"] for item in macro_nutrients if item["name"] == "fats"), 0)
    dish_fibers = next((item["value"] for item in macro_nutrients if item["name"] == "fibers"), 0)

    # To - do 
    # live_goal_protein = user_live_goal["protein"]["value"]
    # live_goal_carbs = user_live_goal["carbs"]["value"]
    # live_goal_fats = user_live_goal["fats"]["value"]
    # live_goal_fibers = user_live_goal["fiber"]["value"]

    live_goal_protein = protien_live_goal_value
    live_goal_carbs = cabs_live_goal_value
    live_goal_fats = fats_live_goal_value
    live_goal_fibers = fiber_live_goal_value

    percentage_difference_protein = percentage_difference["proteins"]
    percentage_difference_carbs = percentage_difference["carbs"]
    percentage_difference_fats = percentage_difference["fats"]
    percentage_difference_fibers = percentage_difference["fibers"]

    #___________________________________________ Dish Nutrients base on percentage ____________________________________________________________________________________________


    live_protien_factor = defult_protien_factor + (defult_protien_factor * percentage_difference_protein /100)
    live_carbs_factor = defult_carbs_factor + (defult_carbs_factor * percentage_difference_carbs /100)
    live_fats_factor = defult_fats_factor + (defult_fats_factor * percentage_difference_fats /100)
    live_fiber_factor = defult_fiber_factor + (defult_fiber_factor * percentage_difference_fibers /100)

    
    protein_live_goal_percentage = (live_goal_protein * 4) / live_goal_energy * 100 or 1
    carbs_live_goal_percentage = (live_goal_carbs * 4) / live_goal_energy * 100 or 1
    fats_live_goal_percentage = (live_goal_fats * 9) / live_goal_energy * 100 or 1
    fiber_live_goal_percentage = (live_goal_fibers * 2) / live_goal_energy * 100 or 1

    print("live_protien_factor", live_protien_factor)
    print("live_carbs_factor", live_carbs_factor)
    print("live_fats_factor", live_fats_factor)
    print("live_fiber_factor", live_fiber_factor)

    score_protein = live_protien_factor * min(1, protien_dish_percentage / protein_live_goal_percentage)
    score_carbs = live_carbs_factor * min(1, cabs_dish_percentage / carbs_live_goal_percentage)
    score_fats = live_fats_factor * min(1, fats_dish_percentage / fats_live_goal_percentage)
    score_fiber = live_fiber_factor * min(1, fiber_dish_percentage / fiber_live_goal_percentage)

    live_base_score_total =  (score_protein + score_carbs + score_fats + score_fiber)

    live_base_score = live_base_score_total * 100 / (live_protien_factor + live_carbs_factor + live_fats_factor + live_fiber_factor + epsilon) 

    #___________________________________________ Euclidean distance __________________________________________________________________________________________________

    protein_euclidean_distance = abs(float(dish_protein) - live_goal_protein)
    carbs_euclidean_distance = abs(float(dish_carbs) - live_goal_carbs)
    fats_euclidean_distance = abs(float(dish_fats) - live_goal_fats)
    fiber_euclidean_distance = abs(float(dish_fibers) - live_goal_fibers)
    print("protein_euclidean_distance",protein_euclidean_distance)
    print("carbs_euclidean_distance",carbs_euclidean_distance)
    print("fats_euclidean_distance",fats_euclidean_distance)
    print("fiber_euclidean_distance",fiber_euclidean_distance)

    
    protein_euclidean = max(0, min(100, (1 - (protein_euclidean_distance / (live_goal_protein + epsilon))) * 100))
    carbs_euclidean = max(0, min(100, (1 - (carbs_euclidean_distance / (live_goal_carbs + epsilon))) * 100))
    fats_euclidean = max(0, min(100, (1 - (fats_euclidean_distance / (live_goal_fats + epsilon))) * 100))
    fiber_euclidean = max(0, min(100, (1 - (fiber_euclidean_distance / (live_goal_fibers + epsilon))) * 100))

    euclidean_distance = protein_euclidean * live_protien_factor + carbs_euclidean * live_carbs_factor + fats_euclidean * live_fats_factor + fiber_euclidean * live_fiber_factor
    euclidean_distance_score = euclidean_distance / (live_protien_factor + live_carbs_factor + live_fats_factor + live_fiber_factor)


    #__________________________________________ Satiety score ________________________________________________________________________________________________________

    protien_variation_percentage = 5
    carbs_variation_percentage = 3
    fats_variation_percentage = 2
    fiber_variation_percentage = 1
    if dish_energy == 0:
        dish_energy = 1
    
    satiety_score = (live_protien_factor * (float(dish_protein) / dish_energy) 
                     + live_carbs_factor * (float(dish_carbs) / dish_energy) 
                     + live_fats_factor * (float(dish_fats) / dish_energy) 
                     + live_fiber_factor * (float(dish_fibers) / dish_energy))

    high_satiety = 1 + high_satiety_factor  * satiety_score
    low_satiety = 1 + low_satiety_factor * satiety_score
    medium_satiety = 1 + medium_satiety_factor * satiety_score

    final_satiety_score = 0

    if hunger_level == "High":
        final_satiety_score = low_satiety
    elif hunger_level == "Low":
        final_satiety_score = high_satiety
    elif hunger_level == "Medium":
        final_satiety_score = medium_satiety

    scaled_satiety_score = (final_satiety_score * 100) / 5 #Assuming the maximum satiety score is 

    # Now all values are between 0 and 1
    final_dish_score = (((live_base_score * density_factor) + (scaled_satiety_score * satiety_factor) + (euclidean_distance_score * euclidean_factor))/ (density_factor + satiety_factor + euclidean_factor))


    return final_dish_score, euclidean_distance_score

# Add a button to rank dishes
if st.button("Rank Dishes"):
    
    st.header("Recommended Dishes")
    UserData = db["UserData"]
    user_data = UserData.find_one({"_id": "user_Rahul Virani_4a11ee11-29ce-47ae-a569-f01c62e03e11"})


    print(user_data)
    hunger_level = user_data["hunger_level"]
    user_default_goal = user_data["goals"]["default_goal"]["nutrients"]
    user_live_goal = user_data["goals"]["live_goal"]["nutrients"]

    default_goal_protein = 20#user_default_goal["protein"]["value"]
    default_goal_carbs = 20#user_default_goal["carbs"]["value"]
    default_goal_fats = 20#user_default_goal["fats"]["value"]
    default_goal_fibers = 10#user_default_goal["fiber"]["value"]

    # live_goal_protein = user_live_goal["protein"]["value"]
    # live_goal_carbs = user_live_goal["carbs"]["value"]
    # live_goal_fats = user_live_goal["fats"]["value"]
    # live_goal_fibers = user_live_goal["fiber"]["value"]

    # live_goal_energy = user_data["goals"]["live_goal"]["kcal"]["value"]
    
    live_goal_protein = protien_live_goal_value
    live_goal_carbs = cabs_live_goal_value
    live_goal_fats = fats_live_goal_value
    live_goal_fibers = fiber_live_goal_value
    live_goal_energy = (protien_live_goal_value * 4) + (cabs_live_goal_value * 4) + (fats_live_goal_value * 9) + (fiber_live_goal_value * 2)
    # percentage_difference_protein = round(((live_goal_protein - default_goal_protein) / default_goal_protein) * 100, 2)
    # percentage_difference_carbs = round(((live_goal_carbs - default_goal_carbs) / default_goal_carbs) * 100, 2)
    # percentage_difference_fats = round(((live_goal_fats - default_goal_fats) / default_goal_fats) * 100, 2)
    # percentage_difference_fibers = round(((live_goal_fibers - default_goal_fibers) / default_goal_fibers) * 100, 2)


    percentage_difference_protein = round(((live_goal_protein - default_goal_protein) / default_goal_protein) * 100, 2) *2
    print("percentage_difference_protein", percentage_difference_protein)
    percentage_difference_carbs = round(((live_goal_carbs - default_goal_carbs) / default_goal_carbs) * 100, 2) *2
    print("percentage_difference_carbs", percentage_difference_carbs)
    percentage_difference_fats = round(((live_goal_fats - default_goal_fats) / default_goal_fats) * 100, 2) *2
    print("percentage_difference_fats", percentage_difference_fats)
    percentage_difference_fibers = round(((live_goal_fibers - default_goal_fibers) / default_goal_fibers) * 100, 2) *2
    print("percentage_difference_fibers", percentage_difference_fibers)

    percentage_difference = {
        "proteins": percentage_difference_protein,
        "carbs": percentage_difference_carbs,
        "fats": percentage_difference_fats,
        "fibers": percentage_difference_fibers
    }



    preferred_types = {"Lunch", "Dinner", "Brunch"}
    ranked_dishes = []

    # Step 1: Score and collect dish info
    for dish in menu_data["menu"]:
        score,euclidean_distance_score = calculate_score(dish, hunger_level, user_live_goal, live_goal_energy, percentage_difference)
        dish_nutrients = extract_nutrients(dish)
        ranked_dishes.append({
            "dish_name": dish["dish_name"],
            "score": score,
            "euclidean_distance_score": euclidean_distance_score,
            "timing_category": dish["timing_category"],
            "nutrients": dish_nutrients,
            "distributed_percentage": dish["distributed_percentage"]
        })

    # Step 2: Sort by score descending
    ranked_dishes.sort(key=lambda x: x["score"], reverse=True)

    # Step 3: Split into top 20%, next 20%, remaining
    total = len(ranked_dishes)
    top_20 = int(total * 0.2)
    next_20 = int(total * 0.2)

    raw_best_match = ranked_dishes[:top_20]
    good_match = ranked_dishes[top_20:top_20 + next_20]
    others = ranked_dishes[top_20 + next_20:]

    # Step 4: Filter best match by preferred dish types
    best_match = []
    moved_to_good = []

    for dish in raw_best_match:
        if set(dish["timing_category"]) & preferred_types:
            best_match.append(dish)
        else:
            moved_to_good.append(dish)

    #random.shuffle(best_match)
    # Add those moved dishes to good match
    good_match = moved_to_good + good_match

    #random.shuffle(good_match)

    # Step 5: Structure final result
    final_result = [
        {
            "category": "Best Match",
            "dishes": best_match
        },
        {
            "category": "Good Match",
            "dishes": good_match
        },
        {
            "category": "Other",
            "dishes": others
        }
    ]

    # Optional: display or return this structure
    st.subheader("🎯 Categorized Dish Recommendations")
    st.json(final_result)

    # Or if returning as response in API:
    # return final_result
