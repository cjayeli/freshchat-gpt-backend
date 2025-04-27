# freshchat-gpt-backend

Freshchat GPT Backend

This project powers a Chrome Extension that suggests smart, fact-based responses for Fido Customer Support agents based on a private knowledge base.

Built with Retrieval-Augmented Generation (RAG) techniques to ensure answers are accurate, professional, and sourced from approved company knowledge.

⸻

📦 Project Structure

/freshchat-gpt-backend/
├── app.py                # Flask server: receives chat, searches knowledge, calls GPT-4
├── embeddings.py         # Embedding script: embeds knowledge files into ChromaDB
├── requirements.txt      # Python dependencies
├── /knowledge/           # (Private) Source text files - NOT committed
├── /vectorstore/         # Embedded knowledge database (ChromaDB) - committed
├── .gitignore            # Protects private files and unwanted junk



⸻

🚀 How It Works
	1.	Agents chat with customers on Freshchat.
	2.	Chrome Extension captures recent customer messages.
	3.	Extension sends the messages to /generate endpoint.
	4.	Backend embeds the customer’s text ➔ searches /vectorstore/ ➔ retrieves relevant knowledge chunks.
	5.	Backend builds a GPT-4 prompt using:
	•	System instructions (Fido support tone, behavior)
	•	Retrieved private knowledge
	6.	GPT-4 returns a suggested response, which agent can edit and send.

⸻

📋 Setup Instructions

1. Install Python dependencies

pip install -r requirements.txt

2. Set your OpenAI API Key (locally, never hardcoded)

export OPENAI_API_KEY=your-openai-key-here

(Or you can use a .env + python-dotenv if you prefer later.)

3. Run the Flask backend locally

python app.py

Or deploy to Render (as you currently do).

4. (When needed) Update the Knowledge Base

When new FAQs or articles are added:

python embeddings.py
git add vectorstore/
git commit -m "Update: refreshed knowledge base embeddings"
git push

✅ Render will auto-redeploy!

⸻

🔒 Security & Privacy Notes
	•	/knowledge/ folder is never committed.
	•	Only /vectorstore/ (embedded vectors) is pushed.
	•	No API keys are hardcoded.
	•	No customer PII stored.

⸻

🛠 Troubleshooting

Issue	Solution
Error connecting to OpenAI	Ensure OPENAI_API_KEY is exported
No suggestions generated	Ensure /vectorstore/ exists and is populated
Chrome Extension CORS error	Confirm Flask CORS settings (already handled)



⸻

📢 Future Enhancements (Optional)
	•	Admin dashboard to upload new files
	•	Auto-refresh embeddings from uploads
	•	Cost optimization strategies (smaller models, batching)
	•	Adding an Audit Trail for generated responses

⸻

✨ Built with ❤️ for Fido Customer Experience Excellence