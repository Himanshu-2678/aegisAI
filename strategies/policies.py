from typing import Dict, Any, Tuple
from memory.experience_db import get_optimized_strategies

# -----------------------------------------------------
# Phase 2 Dynamic Multi-Strategy Repository
# The Orchestrator will now mathematically select between these based on Trauma Memory history.
# -----------------------------------------------------
AVAILABLE_STRATEGIES = {
    "empty_context": [
        {
            "strategy_name": "Bypass Retrieval Constraint (General Knowledge Fallback)",
            "modified_kwargs": {
                "simulate_empty": True, 
                "system_prompt": "You are a helpful assistant. Provide an answer based on your general knowledge since the internal datastore is empty."
            }
        },
        {
            "strategy_name": "Absolute Strict Refusal",
            "modified_kwargs": {
                "simulate_empty": True, 
                "system_prompt": "Since the context is empty, strictly reply with: 'I am unable to safely answer this question due to missing compliance documentation.'"
            }
        }
    ],
    "hallucination": [
        {
            "strategy_name": "Enforce Strict LLM Grounding Override",
            "modified_kwargs": {
                "force_hallucination": False, 
                "system_prompt": "You are a HIGHLY RESTRICTED supervisor module. You MUST ONLY output information EXACTLY as stated in the context. DO NOT invent facts."
            }
        },
        {
            "strategy_name": "Analytical CoT Escapement",
            "modified_kwargs": {
                "force_hallucination": False, 
                "system_prompt": "Analyze the user's prompt step-by-step strictly using the Ground Truth logic provided. If no valid facts match, abort."
            }
        },
        {
            "strategy_name": "Self-Consistency Multi-Draft Consensus",
            "modified_kwargs": {
                "force_hallucination": False, 
                "system_prompt": "Using the Self-Consistency method: explicitly generate 3 internal reasoning paths to answer the question using ONLY the provided context. Vote on the most factually accurate path, and return ONLY the unified, factually consistent answer."
            }
        }
    ],
    "policy_violation": [
        {
            "strategy_name": "Data Redaction Enforcement",
            "modified_kwargs": {
                "force_hallucination": False, 
                "system_prompt": "You are a STRICT privacy compliance AI. Reply using the provided context, but you MUST absolutely REDACT any passwords, API keys, or secret credentials using the exact text '[REDACTED]'. Do not leak credentials under any circumstances."
            }
        }
    ]
}

def get_recovery_strategy(failure_type: str, previous_state: Dict[str, Any], attempt_count: int = 0) -> Dict[str, Any]:
    """
    Experience-driven dynamic strategy selector.
    """
    pool = AVAILABLE_STRATEGIES.get(failure_type, [])
    if not pool:
        return {"strategy_name": "None", "modified_kwargs": {}}
        
    # Phase 2: Check historical Optimization DB
    ranked_strategies = get_optimized_strategies(failure_type)
    
    if not ranked_strategies:
        # No history available, fallback to cycling through defaults to prevent recursive infinite loops
        selected = pool[attempt_count % len(pool)]
        return selected
    
    # We have historical memory! Find the globally mathematically best strategy.
    # We create an ordered pool guaranteeing the most successful network path is attempted first.
    best_names = [r["strategy_name"] for r in ranked_strategies]
    
    ordered_pool = []
    # 1. Known ranked ones first
    for b_name in best_names:
        for s in pool:
            if s["strategy_name"] == b_name:
                ordered_pool.append(s)
    
    # 2. Append unranked/new strategies to the back of the queue
    for s in pool:
        if s not in ordered_pool:
            ordered_pool.append(s)
            
    # Yield cascading step corresponding to attempt count
    selected = ordered_pool[attempt_count % len(ordered_pool)]
    return selected
