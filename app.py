from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import openai
import os

app = Flask(__name__)

# ✅ Allow all origins TEMPORARILY
CORS(app, resources={r"/generate": {"origins": "*"}}, supports_credentials=True)

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        # ✅ Explicit preflight response
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response, 200

    try:
        data = request.get_json(force=True)

        if not isinstance(data, dict):
            print("❌ Expected JSON object, got:", type(data))
            response = jsonify({"error": "Invalid JSON format"})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

        conversation = data.get("conversation", [])
        print("✅ Received conversation:", conversation)

        if not conversation:
            response = jsonify({"suggestions": ["No message history provided."]})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 400

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
        response = jsonify({"suggestions": [reply]})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    except Exception as e:
        print("❌ GPT Error:", str(e))
        response = jsonify({"error": str(e)})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
