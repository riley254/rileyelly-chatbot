from flask import Flask, request, jsonify, render_template
from your_existing_code import handle_query
import requests
import os

app = Flask(__name__)

# Your actual Google API Key and Search Engine ID
GOOGLE_API_KEY = "AIzaSyDopzPpGivVfPAxNZ7MUUYpPDrCFwTtMO8"
SEARCH_ENGINE_ID = "a6f6b0ae48b1048b2"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query", "")

    if query.lower().startswith("search for"):
        search_term = query.replace("search for", "").strip()
        results = google_search(search_term)
        return jsonify({"response": results})
    else:
        response = handle_query(query)
        return jsonify({"response": response})

def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": query
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        items = data.get("items", [])
        if not items:
            return "No results found."
        result_texts = [f"{item['title']}\n{item['link']}" for item in items[:3]]
        return "\n\n".join(result_texts)
    except Exception as e:
        return f"Search error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
