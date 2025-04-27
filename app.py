# app.py (final RAG-ready version)

from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import chromadb
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Load OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path="./vectorstore")

# Connect to your knowledge collection
collection = chroma_client.get_collection(name="fido-support")

# Load Help Center links mapping
import json
help_center_links_path = "knowledge/help_center_links.json"
help_center_links = {}
if os.path.exists(help_center_links_path):
    with open(help_center_links_path, "r", encoding="utf-8") as f:
        help_center_links = json.load(f)

# System prompt based on your instructions
system_prompt = """
You are a virtual assistant for Fido, an African digital bank, specializing in digital lending.
Your role is to assist Fido customer service agents by suggesting relevant responses based on their chat with customers.

- Only provide suggestions using the uploaded knowledge files.
- If you lack sufficient information, politely tell the agent you cannot reliably answer.
- Keep your tone clear, friendly, and professional.
- Be concise and solution-oriented.
- If a process is involved (e.g., loan application, repayment), guide the agent on necessary steps.
- Where applicable, provide a relevant Help Center article link based on provided tags.
- Never invent information or suggest contacting support.
- Maintain a helpful, respectful, and patient tone at all times.

Respond in a way that the agent can send directly to the customer.
"""

@app.route('/generate', methods=['POST', 'OPTIONS'])
def generate():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response, 200

    try:
        data = request.get_json(force=True)
        conversation = data.get("conversation", [])

        if not conversation:
            return jsonify({"suggestions": ["No conversation provided."]}), 400

        # Extract latest customer message
        latest_messages = "\n".join([msg['content'] for msg in conversation if msg['role'] == 'user'])

        # Embed customer message
        embedded_query = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[latest_messages]
        )
        query_embedding = embedded_query.data[0].embedding

        # Retrieve top 3 relevant knowledge chunks
        search_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=['documents']
        )

        retrieved_chunks = search_results['documents'][0] if search_results['documents'] else []

        if not retrieved_chunks:
            context_info = "No relevant knowledge found."
        else:
            context_info = "\n\n".join(retrieved_chunks)

        # Prepare prompt
        messages = [
            {"role": "system", "content": system_prompt + f"\n\nKnowledge Base:\n{context_info}"},
            {"role": "user", "content": latest_messages}
        ]

        # Call GPT-4 for suggestion
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.4
        )

        reply = response.choices[0].message.content.strip()

        return jsonify({"suggestions": [reply]})

    except Exception as e:
        print("❌ Error in /generate:", str(e))
        error_response = jsonify({"error": str(e)})
        error_response.headers['Access-Control-Allow-Origin'] = '*'
        return error_response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
