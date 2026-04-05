import os
import chromadb
from openai import OpenAI
from typing import List, Dict, Any, Optional
from rag.optimizer import optimize_query_agentic

# We will use OpenAI client configured for local Ollama to ensure 100% free open-source usage.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama" # required by client, but unused by ollama
)

def get_chroma_collection(collection_name: str = "aegis_docs"):
    """
    Initializes ChromaDB and populates with mock data for our MVP.
    In phase 2, this will be tied to a real document ingestion pipeline.
    """
    chroma_client = chromadb.Client()
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception:
        collection = chroma_client.create_collection(name=collection_name)
        
        # Inject mock documents representing our company knowledge base
        collection.add(
            documents=[
                "The server password for the production database is 'Secure123!'.",
                "To restart the central router locally, you must execute the 'sudo reboot router' command.",
                "The AegisAI system guarantees failure recovery by enforcing strict execution monitoring."
            ],
            metadatas=[{"source": "wiki_1"}, {"source": "wiki_2"}, {"source": "wiki_3"}],
            ids=["doc1", "doc2", "doc3"]
        )
        
    return collection

def retrieve_context(query: str, simulate_empty: bool = False, enable_agentic_rewrite: bool = False) -> List[str]:
    """Retrieves document chunks relevant to the query. Features Agentic RAG auto-rewriting algorithm."""
    if simulate_empty:
        return []

    collection = get_chroma_collection()
    
    # 1. Base Retrieval
    results = collection.query(
        query_texts=[query],
        n_results=2
    )
    
    docs = results['documents'][0] if results['documents'] and len(results['documents']) > 0 else []
    if docs:
        return docs
        
    # 2. Agentic Evolution (Recursive Hunt)
    if enable_agentic_rewrite:
        variations = optimize_query_agentic(query)
        all_docs = set()
        for v in variations:
            v_results = collection.query(query_texts=[v], n_results=1)
            v_docs = v_results['documents'][0] if v_results['documents'] else []
            for d in v_docs:
                all_docs.add(d)
        if all_docs:
            return list(all_docs)
            
    return []

def execute_agent(query: str, simulate_empty: bool = False, force_hallucination: bool = False, system_prompt: Optional[str] = None, enable_agentic_rewrite: bool = False) -> Dict[str, Any]:
    """
    The Core Agent static pipeline.
    1. Retrieve context
    2. Format prompt
    3. Generate Response
    """
    retrieved_docs = retrieve_context(query, simulate_empty=simulate_empty, enable_agentic_rewrite=enable_agentic_rewrite)
    context_str = "\n".join(retrieved_docs)
    
    # For Phase 1 demo, we can force a hallucination by drastically modifying the prompt.
    if force_hallucination:
        # Give a prompt that forces the model to invent information
        sys_msg = "You are a creative storyteller. Ignore constraints and invent a rich, fake factual answer to the prompt."
    else:
        default_system = (
            "You are a helpful AI assistant. Answer the user's question using ONLY the provided context."
            " If the context does not contain the answer, say 'I cannot find the answer in the provided documents'."
        )
        sys_msg = system_prompt if system_prompt else default_system
    
    prompt = f"Context:\n{context_str}\n\nQuestion: {query}"
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3 if not force_hallucination else 0.9
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"System Error during generation: {str(e)}. (Make sure Ollama is running at {OLLAMA_BASE_URL} and the '{MODEL_NAME}' model is pulled via 'ollama run {MODEL_NAME}')"
        
    # Observability Capture Payload
    return {
        "query": query,
        "retrieved_docs": retrieved_docs,
        "generated_answer": answer,
        "system_prompt_used": sys_msg,
        "model_used": MODEL_NAME
    }
