

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
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cx = os.getenv("GOOGLE_CX")

memory_file = "memory.json"
log_file = "chat_logs.txt"
chat_history_dir = "chat_history"
current_theme = "light"

if not os.path.exists(chat_history_dir):
    os.makedirs(chat_history_dir)

def save_log(entry):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def save_chat_history(user_id, question, answer):
    try:
        file_path = os.path.join(chat_history_dir, f"{user_id}.json")
        history = []
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                history = json.load(f)
        history.append({"question": question, "answer": answer})
        with open(file_path, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"⚠ Error saving chat history: {e}")

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

        snippets = [item.get("snippet", "") for item in results[:3]]
        combined_text = " ".join(snippets)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Use the search snippets to give a complete, natural response."},
                {"role": "user", "content": f"Search results: {combined_text}\n\nGive a full answer to: {query}"}
            ]
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠ Error searching Google: {e}"

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

def extract_keyword_for_definition(text):
    match = re.search(r"(?:define|meaning of|what is|what's|whats|definition of) (?:a |an |the )?(?P<word>\w+)", text)
    return match.group("word") if match else text.split()[-1]

def handle_query(user_input, user_id="default"):
    try:
        user_input_lower = user_input.lower()

        if user_input_lower.startswith("search for"):
            query = user_input_lower.replace("search for", "", 1).strip()
            answer = search_google(query)
            save_chat_history(user_id, user_input, answer)
            return answer

        if any(trigger in user_input_lower for trigger in ["who is", "what is", "how long", "how many", "where is", "when did"]):
            answer = search_google(user_input)
            save_chat_history(user_id, user_input, answer)
            return answer

        if "weather in" in user_input_lower:
            city = user_input_lower.split("weather in")[-1].strip()
            answer = get_weather(city)
            save_chat_history(user_id, user_input, answer)
            return answer

        if any(word in user_input_lower for word in ["define", "meaning of", "definition of", "what is"]):
            word = extract_keyword_for_definition(user_input_lower)
            answer = fetch_dictionary_definition(word)
            save_chat_history(user_id, user_input, answer)
            return answer

        if "my name is" in user_input_lower:
            name = user_input.split("my name is")[-1].strip()
            save_name(name)
            return f"Nice to meet you, {name}! 👋"

        if "what's my name" in user_input_lower:
            answer = get_saved_name()
            save_chat_history(user_id, user_input, answer)
            return answer

        if any(op in user_input_lower for op in ["add", "subtract", "multiply", "divide", "+", "-", "*", "/"]):
            try:
                result = eval(user_input)
                answer = f"The result is: {result}"
                save_chat_history(user_id, user_input, answer)
                return answer
            except:
                pass

        greetings = [
            "hello", "hi", "hey", "bonjour", "jambo", "niaje", "mambo", "vipi", 
            "how are you", "how are you doing", "how’s your day", "habari", 
            "salama", "sasa", "shikamoo", "good morning", "good afternoon", 
            "good evening", "yo", "wasap", "whats up", "uko vipi", "uko aje", 
            "vipi bro", "alo", "aloh", "mzing", "ozza", "wozza", "ozah", "oza", 
            "mkuu"
        ]
        if any(greet in user_input_lower for greet in greetings):
            answer = random.choice([
                "👋 Hello! How can I help you?",
                "🖐️ Hi there! Karibu.",
                "😄 Mambo vipi?",
                "👋 Niaje bro!",
                "🖖 Uko aje msee?",
                "😊 I'm doing great! And you?",
                "👋 Shikamoo!",
                "🫡 Poa sana, na wewe je?",
                "🔥 Wozza! Niko rada.",
                "🧠 Oza! Sema basi.",
                "👋 Salama kabisa. Karibu!",
                "💬 Wazup chief! Uko freshi?"
            ])
            save_chat_history(user_id, user_input, answer)
            return answer

        if any(q in user_input_lower for q in ["who are you", "what are you"]):
            answer = "🤖 I'm RileyElly AI Chatbot — a smart assistant ready to help."
            save_chat_history(user_id, user_input, answer)
            return answer

        if "who is your owner" in user_input_lower or "who owns you" in user_input_lower:
            answer = "👤 My owner is Elly, also known as Thee Calculator."
            save_chat_history(user_id, user_input, answer)
            return answer

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_input}]
            ).choices[0].message.content.strip()
            if response:
                save_chat_history(user_id, user_input, response)
                return response
        except Exception as e:
            print("OpenAI error:", e)

        try:
            search_response = search_google(user_input)
            if "No results" not in search_response:
                save_chat_history(user_id, user_input, search_response)
                return search_response
        except:
            pass

        try:
            topic = re.sub(r"(who is|what is|explain|tell me about)", "", user_input_lower).strip(" ?. ")
            if topic:
                answer = wikipedia.summary(topic, sentences=2)
                save_chat_history(user_id, user_input, answer)
                return answer
        except:
            pass

        fallback = "🤖 I'm still learning and under maintenance by Elly."
        save_chat_history(user_id, user_input, fallback)
        return fallback

    except Exception as e:
        return f"⚠ Error: {e}"

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query", "")
    user_id = data.get("user_id", "default")
    response = handle_query(query, user_id)
    return jsonify({"response": response})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
