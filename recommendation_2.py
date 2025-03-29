import streamlit as st
from datetime import date, datetime
from math import ceil
import json
from datetime import date, datetime
import math
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId

# MongoDB connection details
MONGO_URI = "mongodb://Kishan:KishankFitshield@ec2-13-233-104-209.ap-south-1.compute.amazonaws.com:27017/?authMechanism=SCRAM-SHA-256&authSource=Fitshield"
client = MongoClient(MONGO_URI)
db = client["Fitshield"]

RestaurantMenuData = db["RestaurantMenuData"]

menu_data = RestaurantMenuData.find_one({"_id": "restro_ANAVRIN_395010_40269a87-3a94-4ea3-975d-887e680aac12"})

#print(menu_data)

user_data = {
  "_id": "user_pooja_661e0f7e-92bb-4dd6-8ce8-7037b6918a32",
  "name": "pooja",
  "mobile_number": "9106975484",
  "country_code": "+91",
  "latitude": 0,
  "longitude": 0,
  "created_at": "2025-03-22T10:36:21.902361",
  "updated_at": "2025-03-24T06:41:56.070720",
  "goal": "Muscle Gain",
  "gender": "Female",
  "age": 22,
  "dob": "24-01-2003",
  "height": {
    "value": "157.48",
    "unit": "cm"
  },
  "weight": {
    "value": "51.0",
    "unit": "kg"
  },
  "life_routine": "Sedentary",
  "gym_or_yoga": "Yoga",
  "is_exercise": True,
  "intensity": "Moderate",
  "diet_preference": "Vegetarian",
  "hunger_level": "Low",
  "allergies": [
    "Cereals",
    "Peanuts"
  ],
  "is_personalized": True,
  "goals": {
    "default_goal": {
      "kcal": {
        "value": 814.96,
        "unit": "kcal"
      },
      "nutrients": {
        "carbs": {
          "value": 50,
          "unit": "g"
        },
        "fats": {
          "value": 15,
          "unit": "g"
        },
        "fibers": {
          "value": 10,
          "unit": "g"
        },
        "proteins": {
          "value": 25,
          "unit": "g"
        }
      }
    },
    "live_goal": {
      "kcal": {
        "value": 700,
        "unit": "kcal"
      },
      "nutrients": {
        "carbs": {
          "value": 30,
          "unit": "g"
        },
        "fats": {
          "value": 10,
          "unit": "g"
        },
        "fibers": {
          "value": 5,
          "unit": "g"
        },
        "proteins": {
          "value": 20,
          "unit": "g"
        }
      }
    }
  }
}

default_goal = user_data["goals"]["default_goal"]["nutrients"]
live_goal = user_data["goals"]["live_goal"]["nutrients"]
live_kacl = user_data["goals"]["live_goal"]["kcal"]["value"]
hunger_level = user_data["hunger_level"]

# Extract only the values from the live goal
live_goal_values = {nutrient: details["value"] for nutrient, details in live_goal.items()}

col1, col2, col3, col4 = st.columns(4)  # Creates four smaller columns

with col1:
    protien_goal_value = st.number_input("Proteins %", value=50, step=1, key="protein_input")

with col2:
    cabs_goal_value = st.number_input("Carbs %", value=20, step=1, key="carbs_input")

with col3:
    fats_goal_value = st.number_input("Fats %", value=20, step=1, key="fats_input")

with col4:
    fiber_goal_value = st.number_input("Fibers %", value=10, step=1, key="fiber_input")

col11, col21, col31, col41 = st.columns(4)  # Creates four smaller columns

with col11:
    defult_protien_factor = st.number_input("Density Proteins Factor", value=5, step=1, key="density_protein_input")

with col21:
    defult_carbs_factor = st.number_input("Density Carbs Factor", value=3, step=1, key="density_carbs_input")

with col31:
    defult_fats_factor = st.number_input("Density Fats Factor", value=2, step=1, key="density_fats_input")

with col41:
    defult_fiber_factor = st.number_input("Density Fibers Factor", value=1, step=1, key="density_fiber_input")

col111, col211, col311 = st.columns(3)  # Creates four smaller columns

with col111:
    density_factor = st.number_input("Density Factor", value=0.5, step=0.1, key="density_factor")

with col211:
    satiety_factor = st.number_input("Satiety Factor", value=0.03, step=0.1, key="satiety_factor")

with col311:
    euclidean_factor = st.number_input("Euclidean Factor", value=0.2, step=0.1, key="euclidean_factor")


# Nutrient name mapping from dataset to live goal
nutrient_mapping = {
    "ENERC": "energy",
    "CHOAVLDF": "carbs",
    "FATCE": "fats",
    "FIBTG": "fibers",
    "PROTCNT": "proteins"
}

def extract_nutrients(dish):
    nutrients = dish["dish_variants"]["normal"]["full"]["nutrients"]
    dish_nutrient_values = {nutrient_mapping[n["name"]]: n["quantity"] for n in nutrients if n["name"] in nutrient_mapping}
    return dish_nutrient_values

def calculate_score(dish_energy,dish_nutrients, goal_nutrients,hunger_level,percentage_difference):

    sum = 0

    protien_dish_value = float(dish_nutrients.get("proteins", 0).replace("%", ""))
    
    cabs_dish_value = float(dish_nutrients.get("carbs", 0).replace("%", ""))
    
    fats_dish_value = float(dish_nutrients.get("fats", 0).replace("%", ""))
    
    fiber_dish_value = float(dish_nutrients.get("fibers", 0).replace("%", ""))
   


    defult_satiety_factor = (10 * (defult_protien_factor + defult_carbs_factor + defult_fats_factor + defult_fiber_factor)) / 100
    defult_normalized_factor = 100 / (defult_protien_factor + defult_carbs_factor + defult_fats_factor + defult_fiber_factor + defult_satiety_factor)

    high_satiety_factor = 0.5
    low_satiety_factor = -0.3
    medium_satiety_factor = 0

    protein_e = protien_dish_value - protien_goal_value
    carbs_e = cabs_dish_value - cabs_goal_value
    fats_e = fats_dish_value - fats_goal_value
    fiber_e = fiber_dish_value - fiber_goal_value
    sum_e = protein_e **2 + carbs_e **2 + fats_e **2 + fiber_e **2

    # Calculate Euclidean distance between dish and goal
    euclidean_distance = math.sqrt(sum_e)

    # Euclidean distance factor (adjust this if needed to scale the score)
    #euclidean_factor = 1 / (1 + euclidean_distance)  # Smaller distance, higher factor

    live_protien_factor = defult_protien_factor + (defult_protien_factor * (percentage_difference['proteins']) /100)
    live_carbs_factor = defult_carbs_factor + (defult_carbs_factor * (percentage_difference['carbs']) /100)
    live_fats_factor = defult_fats_factor + (defult_fats_factor * (percentage_difference['fats']) /100)
    live_fiber_factor = defult_fiber_factor + (defult_fiber_factor * (percentage_difference['fibers']) /100)

    protien_variation_per = 5
    carbs_variation_per = 3
    fats_variation_per = 2
    fiber_variation_per = 1
    if dish_energy == 0:
        dish_energy = 1
    satiety_score = protien_variation_per * (protien_dish_value / dish_energy) + carbs_variation_per * (fiber_dish_value / dish_energy) + fats_variation_per * (fats_dish_value / dish_energy) + fiber_variation_per * (cabs_dish_value / dish_energy)

    high_satiety = 1 + high_satiety_factor  * satiety_score
    low_satiety = 1 + low_satiety_factor * satiety_score
    medium_satiety = 1 + medium_satiety_factor * satiety_score

    final_satiety_score = 0

    if hunger_level == "High":
        final_satiety_score = defult_satiety_factor * high_satiety
    elif hunger_level == "Low":
        final_satiety_score = defult_satiety_factor * low_satiety
    elif hunger_level == "Medium":
        final_satiety_score = defult_satiety_factor * medium_satiety

    score_protein = live_protien_factor * (protien_dish_value / protien_goal_value)
    score_carbs = live_carbs_factor * (cabs_dish_value / cabs_goal_value)
    score_fats = live_fats_factor * (fats_dish_value / fats_goal_value)
    score_fiber = live_fiber_factor * (fiber_dish_value / fiber_goal_value)

    live_base_score =  score_protein + score_carbs + score_fats + score_fiber

    # Define min and max values based on observed dataset
    live_base_min = 0
    live_base_max = 100  # Set a realistic max

    final_satiety_min = -0.3 * defult_satiety_factor
    final_satiety_max = 1.5 * defult_satiety_factor

    euclidean_min = 0
    euclidean_max = 100  # Set based on actual data

    # Normalize each score
    live_base_score_norm = (live_base_score - live_base_min) / (live_base_max - live_base_min)
    final_satiety_score_norm = (final_satiety_score - final_satiety_min) / (final_satiety_max - final_satiety_min)
    euclidean_distance_norm = (euclidean_distance - euclidean_min) / (euclidean_max - euclidean_min)

    # Now all values are between 0 and 1
    final_dish_score = (
        (live_base_score_norm * density_factor) +
        (final_satiety_score_norm * satiety_factor) +
        ((1 - euclidean_distance_norm) * euclidean_factor)  # Inverted since lower distance is better
    )

    return final_dish_score

# Add a button to rank dishes
if st.button("Rank Dishes"):
    st.header("Recommended Dishes")

    # Rank dishes based on how closely they match the live goal
    ranked_dishes = []

    percentage_difference = {
        key: round(((live_goal[key]['value'] - default_goal[key]['value']) / default_goal[key]['value']) * 100, 2)
        for key in default_goal
    }

    for dish in menu_data["menu"]:
      dish_nutrients = extract_nutrients(dish)
      energy = dish_nutrients["energy"]
      score = calculate_score(energy,dish["distributed_percentage"], live_goal_values, hunger_level, percentage_difference)
      ranked_dishes.append((dish["dish_name"], score, dish_nutrients,dish["distributed_percentage"]))

    # Sort dishes by highest score
    ranked_dishes.sort(key=lambda x: x[1], reverse=True)
    for rank, (dish, score, dish_nutrients, distributed_percentage) in enumerate(ranked_dishes, 1):
      st.write(f"{rank}. {dish} (Score: {score:.2f})")
      st.json({"Nutrients": dish_nutrients, "Distributed Percentage": distributed_percentage})
