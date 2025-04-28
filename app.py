from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
import os
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app, supports_credentials=True)


# Initialize local embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path="./vectorstore")

# Connect to your knowledge collection
try:
    collection = chroma_client.get_collection(name="fido-support")
except chromadb.errors.NotFoundError:
    collection = chroma_client.create_collection(name="fido-support")

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

        # Embed customer message using local model
        query_embedding = embedder.encode([latest_messages])[0].tolist()

        # Retrieve top 1 relevant knowledge chunk
        search_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
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

        # Simple local response when using only retrieved chunks (no external API)
        reply = retrieved_chunks[0].strip() if retrieved_chunks else "I'm sorry, I couldn't find enough information to confidently suggest a response. Please proceed based on your best judgment."

        return jsonify({"suggestions": [reply]})

    except Exception as e:
        print("❌ Error in /generate:", str(e))
        error_response = jsonify({"error": str(e)})
        error_response.headers['Access-Control-Allow-Origin'] = '*'
        return error_response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), threaded=True, timeout=90)
