from flask import Flask, request, jsonify, render_template
from your_existing_code import handle_query  # ✅ This matches your actual file

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")  # ✅ This must exist in templates/

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    query = data.get("query", "")
    response = handle_query(query)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
