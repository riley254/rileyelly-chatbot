from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Fallback chatbot logic (for now)
def handle_query(query):
    return f"You said: {query}"

@app.route("/")
def home():
    return render_template("index.html")  # index.html must be in the templates/ folder

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query", "")
    response = handle_query(query)
    return jsonify({"response": response})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

