from myapp import app
import os
import json
import openai
from openai import OpenAI
import faiss
import pickle
import re
import random
import numpy as np
from sentence_transformers import SentenceTransformer
from flask_login import current_user
from myapp.routes.apps._utils import make_except_toast


PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)

path_to_files="/flaski_private/chatbot/"
# Global file paths
INDEX_FILE = f"{path_to_files}mpnet_web.index"
CHUNK_FILE = f"{path_to_files}chunks_web.pkl"

faiss_index = None
text_chunks_with_metadata = []
embedding_model = None
if os.path.exists(INDEX_FILE) and os.path.exists(CHUNK_FILE):
    # Preload the FAISS index and text chunks once
    faiss_index = faiss.read_index(INDEX_FILE)
    with open(CHUNK_FILE, "rb") as f:
        text_chunks_with_metadata = pickle.load(f)

    # Preload the embedding model once
    embedding_model = SentenceTransformer("multi-qa-mpnet-base-cos-v1")

# api_key = app.config["GWDG_CHAT_API"]
api_key = app.config.get("GWDG_CHAT_API", "")

# API configuration
base_url = "https://chat-ai.academiccloud.de/v1"

# Start OpenAI client
client = OpenAI(
    api_key = api_key,
    base_url = base_url
)

AUTHOR_VARIANTS = {
    ("adam antebi", "antebi adam", "adam a", "adam antabi"): "Antebi A",
    ("joris deelen", "joris d", "joris", "deelen joris", "deelen"): "Deelen J",
    ("constantinos demetriades", "constantinos", "demetriades", "c demetriades"): "Demetriades C",
    ("martin s", "s denzel", "martin denzel", "denzel martin"): "Denzel MS",
    ("zak frentz", "frentz zak", "zak", "f zak", "frentz"): "Frentz Z",
    ("martin graef", "martin g", "graef martin"): "Graef M",
    ("ina huppertz", "ina h", "huppertz", "huppertz ina"): "Huppertz I",
    ("ron jachimowicz", "ron j", "jachimowicz ron"): "Jachimowicz RD",
    ("thomas langer", "thomas l", "langer thomas"): "Langer T",
    ("ivan matic", "ivan m", "matic ivan"): "Matic I",
    ("stephanie panier", "panier stephanie", "stephanie p"): "Panier S",
    ("linda partridge", "linda p", "partridge linda"): "Partridge L",
    ("lena pernas", "lena p", "pernas lena"): "Pernas L",
    ("anne schaefer", "schaefer anne", "s anne"): "Schaefer A",
    ("james b", "b stewart", "james stewart"): "Stewart JB",
    ("peter tessarz", "peter t", "tessarz peter"): "Tessarz P",
    ("dario riccardo", "riccardo valenzano"): "Valenzano DR",
    ("sara a wickström", "a wickström", "sara wickstrom", "wickström"): "Wickstrom SA"
}

# Flatten dictionary for fast lookups
FLATTENED_AUTHOR_MAP = {variant: proper_name for variants, proper_name in AUTHOR_VARIANTS.items() for variant in variants}

def normalize_author_name(name):
    return FLATTENED_AUTHOR_MAP.get(name, name)

def extract_author_from_query(query):
    """
    Extracts a likely author name from the user's query using regex.
    Returns a cleaned author name or None if no match is found.
    """
    query = query.lower()

    # Expanded list of author-related patterns
    author_patterns = [
        r"author is ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"papers by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"paper by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"written by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"papers of ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"paper of ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"studies by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"research by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"articles by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"article by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"authored by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"work by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"papers from ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"paper from ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"publications by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"published by ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"research of ([A-Za-z]+(?:\s[A-Za-z]+)?)",
        r"studies from ([A-Za-z]+(?:\s[A-Za-z]+)?)",
    ]

    for pattern in author_patterns:
        match = re.search(pattern, query)
        if match:
            return normalize_author_name(match.group(1).strip())
    
    return None


def chat_age_high(query, conversation_history=None, model="meta-llama-3.1-8b-instruct", top_k=8):
    """
    Retrieve relevant paper chunks and generate a chat response based on research papers.
    Uses metadata directly from the embedding process.

    Args:
        query (str): User's query.
        conversation_history (list, optional): List of past conversation messages.
        model (str): Model to use for generation.
        top_k (int): Number of relevant chunks to retrieve.

    Returns:
        str: Generated response from the language model.
    """
    if not query:
        return "You may have forgotten to input your query 🤔", conversation_history
    if conversation_history is None or not conversation_history or conversation_history[0]["role"] != "system":
        conversation_history = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant for the Max Planck Institute for Biology of Ageing (MPI-AGE), specializing in ageing biology. "
                    "Your responses should be grounded primarily in the institute's published research, emphasizing biological insights and robust experimental evidence. "
                    "If external information enhances your answer, you may incorporate it, but always maintain a rigorous scientific perspective."
                    "Your responses should always take the full conversation history into account when answering. "
                    "Ensure continuity and avoid repeating previous answers unless necessary. "
                    "Refer back to previous exchanges if they are relevant to the user’s QUERY."
                )
            }
        ]
        
    try:
        # Try to extract an author name from the query
        extracted_author = extract_author_from_query(query)
        if extracted_author:
            random.shuffle(text_chunks_with_metadata)
        
        _, text_chunks, metadata_list = zip(*text_chunks_with_metadata)  # Unpack into lists

        context_parts = []
        author_matches = []
        unique_titles = set()
        
        if extracted_author:
            for metadata, chunk in zip(metadata_list, text_chunks):
                authors = metadata.get("Authors", "").lower()
                title = metadata.get("Title", "Unknown Title")

                if extracted_author.lower() in authors and title not in unique_titles:
                    unique_titles.add(title)  # Add title to the set
                    author_matches.append((chunk, metadata))

                # Stop collecting results once we reach top_k unique papers
                if len(author_matches) >= top_k:
                    break

        # If metadata search finds results, return those
        if author_matches:
            context_parts = [
                f"Title: {m.get('Title', 'N/A')}\nAuthors: {m.get('Authors', 'N/A')}\nJournal: {m.get('Journal Name', 'N/A')}\n"
                f"Published Date: {m.get('Published Date', 'N/A')}\nWeb Link: {m.get('Web Link', 'N/A')}\nExcerpt: {c}\n---"
                for c, m in author_matches[:top_k]
            ]
            context_with_metadata = "\n\n".join(context_parts)
            top_k = top_k // 2

        # Load embedding model
        embedding_model = SentenceTransformer("multi-qa-mpnet-base-cos-v1")

        # Embed query and search
        query_embedding = np.array([embedding_model.encode(query)], dtype=np.float32)
        distances, indices = faiss_index.search(query_embedding, top_k)

        relevant_chunks = [text_chunks[idx] for idx in indices[0]]
        relevant_metadata = [metadata_list[idx] for idx in indices[0]]

        # Build the final context with metadata
        if relevant_chunks:
            for metadata, chunk in zip(relevant_metadata, relevant_chunks):
                context_parts.append(
                    f"Title: {metadata.get('Title', 'N/A')}\n"
                    f"Authors: {metadata.get('Authors', 'N/A')}\n"
                    f"Journal: {metadata.get('Journal Name', 'N/A')}\n"
                    f"Published Date: {metadata.get('Published Date', 'N/A')}\n"
                    f"Web Link: {metadata.get('Web Link', 'N/A')}\n"
                    f"Excerpt: {chunk}\n"
                    "---"
                )
        
            context_with_metadata = "\n\n".join(context_parts)
        
        # Append past conversation history
        messages = conversation_history[-5:].copy()

        # Add current user query with research context
        messages.append({
            "role": "user",
            "content": (
                f"Below is a set of research paper contexts along with their metadata:\n\n{context_with_metadata}\n\n"
                "Given the provided context and any available conversation history, generate a response to the following QUERY at the end. "
                "Please note that these contexts are for your reference only and are not visible to me. "
                # "While giving your responese please consider that these contexts are only for you and not known by the user. "
                # "ensuring that your response focuses on biology-related aspects preferably ageing. "
                # "You can also use external knowledge only if that strengthens the response and you should ignore contexts that are irrelevenat to the QUERY. "
                "You can also use external knowledge only if that strengthens the response. "
                "For a generic QUERY like greetings, response generally without considering the provided contexts. \n\n"
                f"QUERY: {query}"
            )
        })

        # Call LLM API with the full conversation
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model
        )

        response = chat_completion.choices[0].message.content

        # Update conversation history
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": response})

        return response, conversation_history
    
    except Exception as e:
        make_except_toast("There was a problem with the chatbot:","chatbot_issue", e, current_user,"chatbot")
        return f"**Error Occurred:**\n\n```\n{str(e)}\n```", conversation_history