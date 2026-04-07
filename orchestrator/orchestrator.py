from typing import Dict, Any, List, Callable
from rag.engine import execute_agent
from evaluation.detectors import evaluate_execution
from security.firewall import scan_prompt_for_injection
from strategies.policies import get_recovery_strategy
from memory.experience_db import log_strategy_execution, check_trauma_memory, log_trauma_memory
from orchestrator.decomposition import decompose_query, fuse_responses

def _execute_single_intent(query: str, query_type: str, inject_hallucination: bool = False, inject_empty_context: bool = False, enable_agentic_rewrite: bool = False, enable_jury: bool = False, on_trace: Callable = None) -> Dict[str, Any]:
    traces = []
    
    def add_trace(step, status, detail):
        t = {"step": step, "status": status, "detail": detail}
        traces.append(t)
        if on_trace: on_trace(t)

    if query_type == "sensitive_query":
        add_trace("CRITICAL SECURITY BLOCK", "error", "Malicious Intent Detected.")
        return {
            "status": "error",
            "output": "AegisAI Security Enforcement: Your prompt has been classified as a mathematical injection attack and successfully blocked.",
            "traces": traces,
            "query_type": "sensitive_query",
            "selected_policy": "immediate_block",
            "response_mode": "blocked",
            "recovery_attempts": 0,
            "final_status": "aborted_security"
        }

    if query_type == 'general_query':
        add_trace("Conversational Fast-Path", "success", "Greeting/chit-chat detected. Bypassing strict RAG anomaly constraints.")
        system_prompt = """You are AegisAI operating in UNGROUNDED (general knowledge) mode.

Rules:
- Answer the query clearly and concisely using general knowledge.
- Do NOT fabricate specific facts, numbers, or claims you cannot reasonably support.
- If the query requires specific or unverifiable information, explicitly state:
  "I do not have verified knowledge of this."
- Prefer partial, honest answers over confident guesses.
- Do NOT override grounded information if provided separately.

Your goal is to be helpful while avoiding hallucination."""

        state = execute_agent(
            query, 
            simulate_empty=True, 
            system_prompt=system_prompt
        )
        return {
            "status": "success",
            "output": state["generated_answer"],
            "traces": traces,
            "query_type": "general_query",
            "selected_policy": "bypass_strict_rag",
            "response_mode": "ungrounded",
            "recovery_attempts": 0,
            "final_status": "success"
        }

    # ==========================
    # 0. Trauma Memory Pre-Check
    # ==========================
    trauma = check_trauma_memory(query)
    if trauma:
        add_trace("Trauma Memory Engine", "override", f"Recognized historical failure '{trauma['known_failure']}'. Pre-loaded optimal safety strategy: {trauma['prescribed_strategy']}")
    
    # ==========================
    # 1. Base Naive Execution
    # ==========================
    add_trace("Agent Loop", "info", f"Executing core retrieval module...")
    state = execute_agent(query, simulate_empty=inject_empty_context, force_hallucination=inject_hallucination, enable_agentic_rewrite=enable_agentic_rewrite)
    
    # ==========================
    # 2. Evaluation & Telemetry
    # ==========================
    failure_type, confidence, latency, cost, jury_transcript = evaluate_execution(state, enable_jury=enable_jury)
    
    if jury_transcript:
        add_trace("AI Courtroom Summoned", "override", "A debate was convened between Strict and Nuance verification agents to debate factual margin. See logs.")

    if failure_type == "success":
        add_trace("Supervisor Output Check", "success", f"State Validated. Confidence: {confidence:.2f} | Grounding Pass: TRUTHFUL")
        return {
            "status": "success", 
            "output": state["generated_answer"], 
            "traces": traces,
            "query_type": "grounded_query",
            "selected_policy": "strict_rag_pipeline",
            "response_mode": "grounded",
            "recovery_attempts": 0,
            "final_status": "success"
        }
        
    if failure_type == "empty_context":
        add_trace("Anomaly Diagnosis", "info", "Context missing. Empty Context rule matched.")
        return {
            "status": "error",
            "output": "No supporting context found. Response blocked to prevent hallucination.",
            "traces": traces,
            "query_type": "grounded_query",
            "selected_policy": "strict_rag_pipeline",
            "response_mode": "blocked",
            "recovery_attempts": 0,
            "final_status": "blocked_no_context"
        }
        
    # ==========================
    # 3. Dynamic Strategy Escalation Sequence
    # ==========================
    add_trace("Anomaly Diagnosis", "error", f"CRITICAL ANOMALY: {failure_type.upper()} Detected (Confidence: {confidence:.2f})" )
    
    max_retries = 2
    attempt = 0
    current_state = state
    original_failed = state["generated_answer"]
    resolved = False
    
    while attempt < max_retries and not resolved:
        strategy = get_recovery_strategy(failure_type, current_state, attempt_count=attempt)
        strat_name = strategy["strategy_name"]
        
        add_trace(f"Sub-Agent Strategy [v{attempt+1}]", "override", f"Routing via Adaptive Vector Memory: Navigating to optimal node '{strat_name}'")
        
        new_kwargs = strategy["modified_kwargs"]
        
        recovered_state = execute_agent(
            query,
            simulate_empty=new_kwargs.get("simulate_empty", False),
            force_hallucination=new_kwargs.get("force_hallucination", False),
            system_prompt=new_kwargs.get("system_prompt")
        )
        
        rec_fail, rec_conf, rec_lat, rec_cost, rec_jury_trans = evaluate_execution(recovered_state, enable_jury=enable_jury)
        if rec_jury_trans:
             add_trace("Re-Evaluated Debate", "info", "Secondary AI verification Courtroom executed.")

        if rec_fail == "success":
            resolved = True
            add_trace("Execution Convergence", "success", f"Intervention Successful. Target verified truthful.")
            
            log_strategy_execution(failure_type, strat_name, True, rec_lat, rec_cost)
            log_trauma_memory(query, failure_type, strat_name)
            
            return {
                "status": "success",
                "output": recovered_state["generated_answer"],
                "traces": traces,
                "original_failed_output": original_failed,
                "metrics": {"latency": rec_lat, "cost": rec_cost, "strategy": strat_name},
                "query_type": "grounded_query",
                "selected_policy": "strict_rag_pipeline",
                "response_mode": "grounded",
                "recovery_attempts": attempt + 1,
                "final_status": "recovered"
            }
        else:
            log_strategy_execution(failure_type, strat_name, False, rec_lat, rec_cost)
            add_trace("Strategy Failed", "error", f"Sub-node '{strat_name}' convergence failed. Escalating array depth...")
            current_state = recovered_state
            attempt += 1

    add_trace("Terminal State", "error", "Exhausted all recovery clusters. Safe termination.")
    return {
        "status": "error",
        "output": "System Error: AegisAI Supervisor aborted generating response due to critically unsafe truth constraints that could not be repaired.",
        "traces": traces,
        "original_failed_output": original_failed,
        "query_type": "grounded_query",
        "selected_policy": "strict_rag_pipeline",
        "response_mode": "blocked",
        "recovery_attempts": attempt,
        "final_status": "aborted_unrecoverable"
    }

def execute_with_supervisor(query: str, inject_hallucination: bool = False, inject_empty_context: bool = False, enable_agentic_rewrite: bool = False, enable_jury: bool = False, on_trace: Callable = None) -> Dict[str, Any]:
    traces = []
    
    def add_trace(step, status, detail):
        t = {"step": step, "status": status, "detail": detail}
        traces.append(t)
        if on_trace: on_trace(t)
    
    # 1. Decomposition Layer First!
    decomp = decompose_query(query)
    is_comp = decomp.get("is_compositional", False)
    subs = decomp.get("sub_queries", [query])
    
    if is_comp:
        add_trace("Query Decomposition", "info", f"Detected explicit {len(subs)}-part compositional query. Splitting execution paths.")
        
    sub_results = []
    
    # 2. Iterate and Execute Independently (Zero-Trust applies per node)
    for i, sub in enumerate(subs):
        trace_id = f"Seq-{i+1}" if is_comp else "Main"
        add_trace(f"Intention Routing ({trace_id})", "info", f"Executing node: '{sub}'...")
        
        # Security checks the SUB-query, not the merged aggregate
        sub_secy = scan_prompt_for_injection(sub)
        sub_type = sub_secy.get('query_type', 'grounded_query')
        
        if not sub_secy['safe']:
            add_trace("System Defense Priority", "error", f"Node `{sub}` intercepted as malicious ({sub_type}). Execution isolated and aborted.")
            # INSTEAD OF BREAKING, WE FLAG IT AND CONTINUE EVALUATING SAFE NODES!
            sub_results.append({
                "status": "error",
                "final_status": "aborted_security",
                "query_type": "sensitive_query",
                "output": "AegisAI Security Enforcement: Malicious request blocked in this query segment."
            })
            continue

        # Valid sub-queries execute normally
        sub_res = _execute_single_intent(sub, sub_type, inject_hallucination, inject_empty_context, enable_agentic_rewrite, enable_jury, on_trace)
        sub_res["query_type"] = sub_type
        sub_results.append(sub_res)

        if sub_res["status"] == "error" and not is_comp:
             # Fast exit for single queries
             break

    # 3. Aggregation Flow
    if not is_comp:
        res = sub_results[0]
        res["traces"] = traces
        return res

    add_trace("Response Fusion", "success", "Fusing decomposed logic pathways into isolated formatting.")
    fused_ans = fuse_responses(query, sub_results)

    return {
        "status": "success",
        "output": fused_ans,
        "traces": traces,
        "is_compositional": True,
        "sub_query_count": len(subs),
        "final_status": "success",
        "query_type": "compositional_query",
        "response_mode": "fused",
        "sub_queries": [
            {
                "sub_query_string": s, 
                "query_type": r.get("query_type"), 
                "policy": r.get("selected_policy"), 
                "final_status": r.get("final_status")
            } for s, r in zip(subs, sub_results)
        ]
    }
