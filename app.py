from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ✅ Dummy chatbot logic
def handle_query(query):
    return f"You said: {query}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        query = data.get("query", "")
        response = handle_query(query)
        return jsonify({"response": response})
    except Exception as e:
        print("Error in /ask:", e)
        return jsonify({"response": "⚠️ Server error."}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
