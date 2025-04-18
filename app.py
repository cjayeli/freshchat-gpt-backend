# app.py (Updated with Logging and Test Route)
from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
import logging # <-- Import logging

# --- Setup basic logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
# ---

app = Flask(__name__)
CORS(app)

logging.info("Flask app initializing...") # <-- Log startup

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
logging.info("OpenAI client initialized.") # <-- Log after client init

# --- Add a simple test route for '/' ---
@app.route('/', methods=['GET'])
def root():
    logging.info("Root route '/' accessed.") # <-- Log access to '/'
    return jsonify({"message": "Backend is running!"})
# ---

@app.route('/generate', methods=['POST'])
def generate():
    logging.info("'/generate' route accessed.") # <-- Log access to '/generate'
    try:
        # --- Keep existing print statements for now, add logging ---
        data = request.get_json(force=True)
        logging.info(f"Received request data type: {type(data)}")

        if not isinstance(data, dict):
            logging.error(f"Invalid JSON format received: {type(data)}") # <-- Log error
            print("❌ Expected JSON object, got:", type(data))
            return jsonify({"error": "Invalid JSON format"}), 400

        conversation = data.get("conversation", [])
        logging.info(f"Received conversation length: {len(conversation)}") # <-- Log conversation info
        print("✅ Received conversation:", conversation) # Keep for now

        if not conversation:
            logging.warning("No message history provided.") # <-- Log warning
            return jsonify({"suggestions": ["No message history provided."]}), 400

        messages = [
            {
                "role": "system",
                "content": "You are a helpful customer support assistant. Reply based only on recent customer messages after CSAT."
            }
        ] + conversation

        logging.info("Calling OpenAI API...") # <-- Log before API call
        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        logging.info("Received response from OpenAI API.") # <-- Log after API call

        reply = gpt_response.choices[0].message.content.strip()
        return jsonify({ "suggestions": [reply] })

    except Exception as e:
        logging.exception("An error occurred in /generate endpoint") # <-- Log exception with traceback
        print("❌ GPT Error:", str(e)) # Keep for now
        return jsonify({ "error": str(e) }), 500

logging.info("Flask app routes defined.") # <-- Log after routes

# Note: The if __name__ == '__main__': block is not executed by Gunicorn
# Gunicorn imports the 'app' object directly.
# So, the logging.info below won't appear when running with Gunicorn.
if __name__ == '__main__':
    logging.info("Starting Flask development server (for local testing only)...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
