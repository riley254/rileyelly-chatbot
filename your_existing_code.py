
import json
import os
import random
from dotenv import load_dotenv
from datetime import datetime
import openai
import requests
import wikipedia
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import re
from flask import Flask, request, jsonify, render_template

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")  # ✅ Added
google_cx = os.getenv("GOOGLE_CX")              # ✅ Added

memory_file = "memory.json"
log_file = "chat_logs.txt"
current_theme = "light"

# Save chat log
def save_log(entry):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

# Dictionary API
def fetch_dictionary_definition(word):
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            meaning = data[0]['meanings'][0]['definitions'][0]['definition']
            return meaning
        else:
            return "❌ Sorry, I couldn't find the meaning."
    except Exception as e:
        return f"⚠ Error fetching definition: {e}"

# Weather API
def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get("main"):
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"The weather in {city.title()} is {temp}°C with {desc}."
        else:
            return "⚠ City not found or weather unavailable."
    except Exception as e:
        return f"⚠ Error fetching weather: {e}"

# Google Custom Search API
def search_google(query):
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": google_api_key,
            "cx": google_cx,
            "q": query
        }
        response = requests.get(url, params=params)
        results = response.json().get("items", [])
        if not results:
            return "❌ No results found."
        top_result = results[0]
        title = top_result["title"]
        snippet = top_result.get("snippet", "")
        link = top_result["link"]
        return f"🔎 {title}\n{snippet}\n🔗 {link}"
    except Exception as e:
        return f"⚠ Error searching Google: {e}"

# Save and get user name
def save_name(name):
    try:
        with open(memory_file, "w") as f:
            json.dump({"name": name}, f)
    except:
        pass

def get_saved_name():
    try:
        if os.path.exists(memory_file):
            with open(memory_file, "r") as f:
                data = json.load(f)
                return f"Your name is {data.get('name', 'unknown')}"
        else:
            return "I don’t know your name yet!"
    except:
        return "⚠ Error reading memory."

# Handle input
def handle_query(user_input):
    try:
        user_input_lower = user_input.lower()

        if user_input_lower.startswith("search for"):
            query = user_input_lower.replace("search for", "", 1).strip()
            return search_google(query)

        if "weather" in user_input_lower:
            city = user_input_lower.split("weather in")[-1].strip()
            return get_weather(city)

        elif any(word in user_input_lower for word in ["hello", "hi", "hey", "bonjour", "jambo", "niaje"]):
            greetings = [
                "👋 Hello! How can I help you?",
                "👋 Hi there! What can I do for you?",
                "👋 Hey! Need any help?",
                "👋 Bonjour! Comment puis-je vous aider?",
                "👋 Jambo rafiki! Nifanye nini leo?",
                "👋 Niaje! Niko rada, sema basi!"
            ]
            return random.choice(greetings)

        elif any(op in user_input_lower for op in ["add", "subtract", "multiply", "divide", "+", "-", "*", "/"]):
            try:
                result = eval(user_input)
                return f"The result is: {result}"
            except Exception as e:
                return f"⚠ Could not calculate: {e}"

        elif "define" in user_input_lower:
            match = re.search(r"(?:define|meaning of|what is) (?:a |an |the )?(?P<word>\w+)", user_input_lower)
            word = match.group("word") if match else user_input_lower.split("define")[-1].strip()
            return fetch_dictionary_definition(word)

        elif any(phrase in user_input_lower for phrase in ["who is", "what is"]) or len(user_input_lower.split()) >= 2:
            try:
                topic = re.sub(r"(who is|what is|explain|tell me about)", "", user_input_lower).strip(" ?. ")
                if topic:
                    summary = wikipedia.summary(topic, sentences=2)
                    return summary
                else:
                    return "❓ Please provide a topic to search."
            except wikipedia.exceptions.DisambiguationError as e:
                return f"❗ That topic is too broad. Try being more specific like '{e.options[0]}'"
            except wikipedia.exceptions.PageError:
                return "❌ I couldn't find any Wikipedia page for that."
            except Exception as e:
                return f"⚠ Error fetching info: {e}"

        elif "my name is" in user_input_lower:
            name = user_input.split("my name is")[-1].strip()
            save_name(name)
            return f"Nice to meet you, {name}! 👋"

        elif "what's my name" in user_input_lower:
            return get_saved_name()

        elif "science" in user_input_lower or "history" in user_input_lower:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_input}]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"⚠ GPT Error: {e}"

        else:
            return "🤖 I'm not sure, but I'm learning! Try asking about science, math, weather, or say 'define [word]'."
    except Exception as e:
        return f"⚠ Error in logic: {e}"

# Flask API
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query", "")
    response = handle_query(query)
    return jsonify({"response": response})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
