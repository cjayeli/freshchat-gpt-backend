# app.py (Restore original /generate logic)
from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app) # Allows all origins by default

logging.info("Flask app initializing...")

# Ensure API key is loaded - check Render env vars if issues arise
client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
logging.info("OpenAI client initialized.")

@app.route('/', methods=['GET'])
def root():
    logging.info("Root route '/' accessed.")
    return jsonify({"message": "Backend is running!"})

# Restore original /generate route - remove GET if no longer needed for testing
@app.route('/generate', methods=['POST'])
def generate():
    # Log entry point - Method logging is less useful now
    logging.info("'/generate' route accessed.")
    try:
        # Use force=True cautiously, ensure client sends correct Content-Type
        data = request.get_json(force=True)
        logging.info(f"Received request data type: {type(data)}")

        if not isinstance(data, dict):
            logging.error(f"Invalid JSON format received: {type(data)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        conversation = data.get("conversation", [])
        logging.info(f"Received conversation length: {len(conversation)}")

        if not conversation:
            logging.warning("No message history provided.")
            # Return the structure expected by the frontend
            return jsonify({"suggestions": ["No message history provided."]}), 200 # 200 OK might be better

        messages = [
            {
                "role": "system",
                "content": "You are a helpful customer support assistant. Reply based only on recent customer messages after CSAT."
            }
        ] + conversation

        logging.info("Calling OpenAI API...")
        gpt_response = client.chat.completions.create(
            model="gpt-4", # Make sure this model is appropriate/available
            messages=messages,
            temperature=0.7
        )
        logging.info("Received response from OpenAI API.")

        reply = gpt_response.choices[0].message.content.strip()
        # *** Return the correct structure ***
        return jsonify({ "suggestions": [reply] })

    except Exception as e:
        logging.exception("An error occurred in /generate endpoint")
        # Return error structure
        return jsonify({ "error": f"An error occurred: {str(e)}" }), 500

logging.info("Flask app routes defined.")

# Gunicorn runs the 'app' object, this part below is not executed by Gunicorn
