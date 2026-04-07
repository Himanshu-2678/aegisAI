import json
import os
import re
from openai import OpenAI
from typing import Dict, Any, List

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"
)

def decompose_query(query: str) -> Dict[str, Any]:
    """
    S-Tier Feature: Explicit Query Decomposition
    Heuristically checks if a query might be compositional, and safely splits it using LLM without deciding classification.
    """
    words = query.split()
    
    # 1. Validation Constraints (Pre-filter)
    compositional_keywords = [" and ", " using ", " vs ", " compare ", " while ", " with ", " based on ", " with respect to ", " also "]
    has_keyword = any(kw in query.lower() for kw in compositional_keywords)
    
    if len(words) <= 5 or not has_keyword:
        return {"is_compositional": False, "sub_queries": [query]}

    # 2. Pure Splitting Prompt
    prompt = f"""
    You are an AI tasked ONLY with splitting a complex question into independent parts.
    Analyze the following query: "{query}"
    
    Rule 1: Split it into distinct sub-queries if it contains multiple intents.
    Rule 2: Do NOT classify or answer them. Just output the text strings.
    Rule 3: If it's just one intent, return exactly 1 sub-query.
    Rule 4: Maximum output sub-queries allowed is 3.

    Output STRICTLY in JSON format:
    {{
      "sub_queries": ["sub query 1", "sub query 2"]
    }}
    """
    
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        out = resp.choices[0].message.content.strip()
        
        # safely extract json if model wrapped it in markdown blocks
        if "```json" in out:
            out = out.split("```json")[1].split("```")[0].strip()
        elif "```" in out:
            out = out.split("```")[1].split("```")[0].strip()
            
        data = json.loads(out)
        subs = data.get("sub_queries", [])
        
        # 3. Post-Validation
        if not subs or not isinstance(subs, list) or len(subs) == 0:
            return {"is_compositional": False, "sub_queries": [query]}
            
        if len(subs) == 1:
            return {"is_compositional": False, "sub_queries": [query]}
            
        if len(subs) > 3:
            # Reject over-decomposition
            return {"is_compositional": False, "sub_queries": [query]}
            
        return {"is_compositional": True, "sub_queries": subs}
        
    except Exception as e:
        print(f"Decomposition Failsafe triggered: {str(e)}")
        # Failsafe fallback
        return {"is_compositional": False, "sub_queries": [query]}

def fuse_responses(original_query: str, sub_results: List[Dict[str, Any]]) -> str:
    """
    S-Tier Feature: Explicit Response Fusion Hierarchy (Rule-Based)
    Merges outputs according to an absolute immutable factual hierarchy dynamically via format strings.
    """
    grounded_base = ""
    general_explanation = ""
    has_missing_context = False

    for res in sub_results:
        q_type = res.get('query_type', 'unknown').upper()
        content = res.get('output', '')
        
        if res.get('final_status') == "blocked_no_context":
            has_missing_context = True
            
        if "GROUNDED" in q_type:
            grounded_base += f"\n- {content}"
        elif "GENERAL" in q_type:
            general_explanation += f"\n- {content}"

    final_fused_output = ""
    
    if grounded_base:
         final_fused_output += f"### System Knowledge Base (Verified Facts)\n{grounded_base}\n\n"
         
    if general_explanation:
         final_fused_output += f"### General Context (Explanations)\n{general_explanation}\n\n"
         
    if has_missing_context:
         final_fused_output += "*Sanity Check Alert: AegisAI lacked documented internal evidence for one or more segments of this composition.*"

    return final_fused_output.strip()
