import os
import json
from typing import List
from openai import OpenAI

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"
)

def optimize_query_agentic(query: str) -> List[str]:
    """
    S-Tier Feature: Auto-Evolving Agentic RAG.
    If the first retrieval fails, this sub-agent autonomously rewrites the human query 
    into 3 distinct, highly optimized mathematical search strings to aggressively hunt missing context.
    """
    prompt = f"""
    You are an expert vector search-engine query optimizer for an enterprise AI system. 
    The following user query failed to retrieve results from our private database.
    Your task is to mathematically rewrite this query into 3 distinct, keyword-heavy search permutations to maximize vector semantic similarity chances.
    
    Original Human Query: {query}
    
    Output exactly 3 variations, one per line, starting with "1. ", "2. ", "3. ".
    Do not output any other text or conversational filler.
    """
    
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        variations_text = resp.choices[0].message.content.strip()
        
        variations = []
        for line in variations_text.split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and ". " in line:
                variations.append(line.split(". ", 1)[1].strip())
        
        # Fallback if structural constraint failed
        if not variations:
            variations = [query, query + " keywords", query + " data context"]
            
        return variations[:3]
    except Exception:
        # Failsafe identity
        return [query]
