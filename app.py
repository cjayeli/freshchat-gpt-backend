# app.py (Updated - Simplify /generate)
from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app)

logging.info("Flask app initializing...")

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
logging.info("OpenAI client initialized.")

@app.route('/', methods=['GET'])
def root():
    logging.info("Root route '/' accessed.")
    return jsonify({"message": "Backend is running!"})

# --- Simplified /generate route ---
@app.route('/generate', methods=['POST'])
def generate():
    logging.info("'/generate' route accessed. SIMPLIFIED VERSION.") # <-- Log access
    # Comment out ALL original logic for now
    # try:
    #    data = request.get_json(force=True)
    #    logging.info(f"Received request data type: {type(data)}")
    #    # ... rest of original code ...
    # except Exception as e:
    #    logging.exception("An error occurred in /generate endpoint")
    #    print("❌ GPT Error:", str(e)) # Keep for now
    #    return jsonify({ "error": str(e) }), 500
    return jsonify({"message": "Generate endpoint reached (simplified)"}) # <-- Return simple success
# --- End of simplified route ---

logging.info("Flask app routes defined.")

# Note: The if __name__ == '__main__': block is not executed by Gunicorn
