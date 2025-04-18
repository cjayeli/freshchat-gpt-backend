from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)

# ✅ Allow any origin for now (for debugging); you can restrict later
CORS(app, resources={r"/generate": {"origins": "*"}}, supports_credentials=True)

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        # ✅ Respond to CORS preflight request
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response, 200

    try:
        # ✅ Parse JSON body
        data = request.get_json(force=True)

        if not isinstance(data, dict):
            print("❌ Expected JSON object, got:", type(data))
            return jsonify({"error": "Invalid JSON format"}), 400

        conversation = data.get("conversation", [])
        print("✅ Received conversation:", conversation)

        if not conversation:
            return jsonify({"suggestions": ["No message history provided."]}), 400

        messages = [
            {
                "role": "system",
                "content": "You are a helpful customer support assistant. Reply based only on recent customer messages after CSAT."
            }
        ] + conversation

        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
        json_response = jsonify({ "suggestions": [reply] })
        json_response.headers.add("Access-Control-Allow-Origin", "*")  # ✅ fallback CORS header
        return json_response

    except Exception as e:
        print("❌ GPT Error:", str(e))
        error_response = jsonify({ "error": str(e) })
        error_response.headers.add("Access-Control-Allow-Origin", "*")  # ✅ fallback CORS header
        return error_response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
