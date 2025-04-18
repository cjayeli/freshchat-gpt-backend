from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    conversation = data.get("conversation", [])

    if not conversation:
        return jsonify({"suggestions": ["No message history provided."]}), 400

    messages = [
        {"role": "system", "content": "You are a helpful customer support assistant. Reply based only on recent customer messages after CSAT."}
    ] + conversation

    try:
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    temperature=0.7
)

reply = response.choices[0].message.content.strip()
        return jsonify({"suggestions": [reply]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Bind to 0.0.0.0 to allow external access on Render
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
