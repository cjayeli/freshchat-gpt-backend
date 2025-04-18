# app.py (Updated)
from flask import Flask, request, jsonify # Removed make_response as it's not used
import openai
import os
from flask_cors import CORS # <-- Import CORS

app = Flask(__name__)
CORS(app) # <-- Initialize CORS for your app

# Remove the manual @app.after_request decorator below
# @app.after_request
# def apply_cors_headers(response):
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
#     response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
#     return response

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Remove 'OPTIONS' from methods and the explicit check, Flask-CORS handles it
@app.route('/generate', methods=['POST'])
def generate():
    # No need for: if request.method == 'OPTIONS': return jsonify({}), 200

    try:
        data = request.get_json(force=True)

        if not isinstance(data, dict):
            print("❌ Expected JSON object, got:", type(data))
            return jsonify({"error": "Invalid JSON format"}), 400

        conversation = data.get("conversation", [])
        print("✅ Received conversation:", conversation)

        if not conversation:
             # Consider if 400 is right, or maybe 200 with an empty suggestion?
            return jsonify({"suggestions": ["No message history provided."]}), 400

        messages = [
            {
                "role": "system",
                "content": "You are a helpful customer support assistant. Reply based only on recent customer messages after CSAT."
            }
        ] + conversation

        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )

        reply = gpt_response.choices[0].message.content.strip()
        return jsonify({ "suggestions": [reply] })

    except Exception as e:
        print("❌ GPT Error:", str(e))
        # Flask-CORS usually adds headers to error responses too
        return jsonify({ "error": str(e) }), 500

if __name__ == '__main__':
    # Render uses its own web server (like Gunicorn usually),
    # so this app.run is mainly for local testing.
    # Render uses the startCommand from render.yaml: "python app.py"
    # Ensure the production server handles requests correctly.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
