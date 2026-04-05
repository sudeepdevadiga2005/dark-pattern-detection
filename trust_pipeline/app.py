from flask import Flask, jsonify, request
from trust_pipeline.datasets import load_datasets
from trust_pipeline.pipeline import analyze_input

app = Flask(__name__)

# Preload required datasets into memory for fast querying
load_datasets()

@app.route("/api/analyze", methods=["POST"])
def analyze_api():
    try:
        data = request.get_json(force=True)
        user_input = data.get("input", "") or data.get("url", "") or data.get("text", "")

        result = analyze_input(user_input)
        return jsonify({
            "success": True,
            "result": result
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Analysis failed due to a server error.",
            "error": str(e)
        }), 500

if __name__ == "__main__":
    # Start the standalone server on localhost:5000
    app.run(debug=True, port=5000)
