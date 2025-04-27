# embeddings.py

import os
from openai import OpenAI
import chromadb
from uuid import uuid4
import tiktoken
import sys

# Function to count tokens
def num_tokens_from_string(string, model="text-embedding-ada-002"):
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(string))

# Function to chunk text into smaller pieces
def chunk_text(text, max_tokens=8000):
    """Split text into chunks smaller than max_tokens."""
    # First attempt: Split by double newlines to preserve paragraph structure
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    # Initial token counting to see if we need more aggressive chunking
    largest_paragraph_tokens = max([num_tokens_from_string(p) for p in paragraphs]) if paragraphs else 0
    total_tokens = num_tokens_from_string(text)
    
    # If text is very large, use a more aggressive max_tokens threshold
    original_max_tokens = max_tokens
    if total_tokens > 10000:
        max_tokens = min(max_tokens, 4000)  # Use smaller chunks for very large documents
    
    print(f"Document with {total_tokens} tokens, largest paragraph has {largest_paragraph_tokens} tokens. Using max_tokens={max_tokens}")
    
    chunks = []
    current_chunk = ""
    
    # Process paragraphs
    for paragraph in paragraphs:
        # Check if this single paragraph is already too large
        paragraph_tokens = num_tokens_from_string(paragraph)
        if paragraph_tokens > max_tokens:
            # This paragraph alone is too big, we need to split it further
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Split by sentences for large paragraphs
            sentences = []
            # Split by common sentence terminators
            for terminator in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                paragraph = paragraph.replace(terminator, terminator + '[SPLIT]')
            
            for s in paragraph.split('[SPLIT]'):
                s = s.strip()
                if s:
                    sentences.append(s)
            
            # Process sentences
            current_sentence_chunk = ""
            for sentence in sentences:
                sentence_tokens = num_tokens_from_string(sentence)
                
                # If this single sentence is too large
                if sentence_tokens > max_tokens:
                    # If we've accumulated sentences, add them first
                    if current_sentence_chunk:
                        chunks.append(current_sentence_chunk)
                        current_sentence_chunk = ""
                    
                    # Split by words for large sentences
                    words = sentence.split()
                    current_word_chunk = ""
                    for word in words:
                        potential_chunk = current_word_chunk + " " + word if current_word_chunk else word
                        if num_tokens_from_string(potential_chunk) > max_tokens:
                            if current_word_chunk:
                                chunks.append(current_word_chunk)
                                current_word_chunk = word
                            else:
                                # If a single word is somehow too large (rare), 
                                # we'll have to split it into characters (very rare)
                                chunks.append(word[:len(word)//2])
                                chunks.append(word[len(word)//2:])
                        else:
                            current_word_chunk = potential_chunk
                    
                    if current_word_chunk:
                        chunks.append(current_word_chunk)
                
                # Normal sized sentence
                else:
                    potential_chunk = current_sentence_chunk + " " + sentence if current_sentence_chunk else sentence
                    if num_tokens_from_string(potential_chunk) > max_tokens:
                        chunks.append(current_sentence_chunk)
                        current_sentence_chunk = sentence
                    else:
                        current_sentence_chunk = potential_chunk
            
            # Add any remaining sentence chunk
            if current_sentence_chunk:
                chunks.append(current_sentence_chunk)
        
        # Handle normal sized paragraphs
        else:
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            if num_tokens_from_string(potential_chunk) > max_tokens:
                chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk = potential_chunk
    
    # Don't forget to add the last chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    # Final check for any chunks that are still too large (this shouldn't happen with our logic,
    # but it's a safety check)
    final_chunks = []
    for chunk in chunks:
        chunk_tokens = num_tokens_from_string(chunk)
        if chunk_tokens > original_max_tokens:
            print(f"Warning: Chunk with {chunk_tokens} tokens is still too large. Forcing split.")
            # Force split into roughly equal parts
            words = chunk.split()
            mid = len(words) // 2
            final_chunks.append(" ".join(words[:mid]))
            final_chunks.append(" ".join(words[mid:]))
        else:
            final_chunks.append(chunk)
    
    print(f"Split document into {len(final_chunks)} chunks")
    return final_chunks

# Configure OpenAI - Using the new OpenAI client with environment variable
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set.")
    print("Please set it using 'export OPENAI_API_KEY=your-key-here' and run the script again.")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# Initialize ChromaDB - Updated configuration for new Chroma version
chroma_client = chromadb.PersistentClient(path="vectorstore")

# Create or get a collection
collection = chroma_client.get_or_create_collection(name="knowledge_base")

# Load all knowledge base text files
knowledge_dir = "knowledge"
documents = []

for filename in os.listdir(knowledge_dir):
    if filename.endswith(".txt"):
        filepath = os.path.join(knowledge_dir, filename)
        print(f"Processing file: {filename}")
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
            # Use the new chunking function instead of simple splitting
            text_chunks = chunk_text(text)
            # Only keep chunks that have a reasonable length
            valid_chunks = [chunk for chunk in text_chunks if len(chunk) > 40]
            documents.extend(valid_chunks)

print(f"✅ Loaded {len(documents)} chunks from knowledge base.")

# Embed and store
successful_embeds = 0
failed_embeds = 0

for idx, doc in enumerate(documents):
    try:
        # Check token count before embedding
        token_count = num_tokens_from_string(doc)
        if token_count > 8000:
            print(f"⚠️ Document chunk {idx} is still too large ({token_count} tokens). Skipping.")
            failed_embeds += 1
            continue
            
        # Using the new OpenAI embedding API format
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=doc
        )
        embedding = response.data[0].embedding

        collection.add(
            embeddings=[embedding],
            documents=[doc],
            ids=[str(uuid4())]  # Use UUID to avoid duplicate key errors
        )
        successful_embeds += 1
        
        # Print progress every 10 embeddings
        if successful_embeds % 10 == 0:
            print(f"Progress: {successful_embeds}/{len(documents)} documents embedded")
            
    except Exception as e:
        print(f"❌ Error embedding document {idx}: {e}")
        failed_embeds += 1

print(f"🎯 Embedding complete! {successful_embeds} documents successfully embedded, {failed_embeds} failed.")
