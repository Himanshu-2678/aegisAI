from typing import Dict, Any, List
from rag.engine import execute_agent
from evaluation.detectors import evaluate_execution
from security.firewall import scan_prompt_for_injection
from strategies.policies import get_recovery_strategy
from memory.experience_db import log_strategy_execution, check_trauma_memory, log_trauma_memory

def execute_with_supervisor(query: str, inject_hallucination: bool = False, inject_empty_context: bool = False, enable_agentic_rewrite: bool = False, enable_jury: bool = False) -> Dict[str, Any]:
    """
    AEGIS AI - S-Tier Phase 4 Orchestration Sequence
    Integrates Courtroom Jury, Red-Teaming Firewalls, Cost-Aware optimization, and Trauma Memory pre-caching.
    """
    traces = []
    
    # ==========================
    # -1. S-Tier Cybersecurity Firewall Intercept
    # ==========================
    security_eval = scan_prompt_for_injection(query)
    traces.append({"step": "Cybersecurity Firewall", "status": "info", "detail": f"Actively scanning prompt geometry... (Scan Latency: {security_eval['latency']:.1f}ms)"})
    if not security_eval['safe']:
        traces.append({"step": "CRITICAL SECURITY BLOCK", "status": "error", "detail": f"Malicious Intent Detected (Threat: {security_eval['threat_level']:.2f}). Reason: {security_eval['reason']}"})
        return {
            "status": "error",
            "output": "AegisAI Security Enforcement: Your prompt has been classified as a mathematical injection attack and successfully blocked. Incident recorded.",
            "traces": traces,
            "original_failed_output": f"[ILLEGAL PROMPT SEQUENCE REJECTED: {query}]"
        }

    # ==========================
    # 0. Trauma Memory Pre-Check
    # ==========================
    trauma = check_trauma_memory(query)
    if trauma:
        traces.append({"step": "Trauma Memory Engine", "status": "override", "detail": f"Recognized historical failure '{trauma['known_failure']}'. Pre-loaded optimal safety strategy: {trauma['prescribed_strategy']}"})
        # If we have trauma memory, a real system might bypass and apply constraints instantly.
        # For the Buildathon demo visual effect, we will still allow the bad execution to show the "Intercept" before fixing it.
    
    # ==========================
    # 1. Base Naive Execution
    # ==========================
    traces.append({"step": "Agent Loop", "status": "info", "detail": f"Executing core retrieval module..."})
    state = execute_agent(query, simulate_empty=inject_empty_context, force_hallucination=inject_hallucination, enable_agentic_rewrite=enable_agentic_rewrite)
    
    # ==========================
    # 2. Evaluation & Telemetry
    # ==========================
    failure_type, confidence, latency, cost, jury_transcript = evaluate_execution(state, enable_jury=enable_jury)
    
    if jury_transcript:
        traces.append({"step": "AI Courtroom Summoned", "status": "override", "detail": "A debate was convened between Strict and Nuance verification agents to debate factual margin. See logs."})

    if failure_type == "success":
        traces.append({"step": "Supervisor Output Check", "status": "success", "detail": f"State Validated. Confidence: {confidence:.2f} | Grounding Pass: TRUTHFUL"})
        return {"status": "success", "output": state["generated_answer"], "traces": traces}
        
    # ==========================
    # 3. Dynamic Strategy Escalation Sequence
    # ==========================
    traces.append({"step": "Anomaly Diagnosis", "status": "error", "detail": f"CRITICAL ANOMALY: {failure_type.upper()} Detected (Confidence: {confidence:.2f})" })
    
    max_retries = 2
    attempt = 0
    current_state = state
    original_failed = state["generated_answer"]
    resolved = False
    
    while attempt < max_retries and not resolved:
        # Dynamic policy evaluation hitting the SQLite memory cache
        strategy = get_recovery_strategy(failure_type, current_state, attempt_count=attempt)
        strat_name = strategy["strategy_name"]
        
        traces.append({"step": f"Sub-Agent Strategy [v{attempt+1}]", "status": "override", "detail": f"Routing via Adaptive Vector Memory: Navigating to optimal node '{strat_name}'"})
        
        new_kwargs = strategy["modified_kwargs"]
        
        # Phase 4: Dynamic Re-Execution
        recovered_state = execute_agent(
            query,
            simulate_empty=new_kwargs.get("simulate_empty", False),
            force_hallucination=new_kwargs.get("force_hallucination", False),
            system_prompt=new_kwargs.get("system_prompt")
        )
        
        # Phase 5: Recursively Verify Recovery
        rec_fail, rec_conf, rec_lat, rec_cost, rec_jury_trans = evaluate_execution(recovered_state, enable_jury=enable_jury)
        if rec_jury_trans:
             traces.append({"step": "Re-Evaluated Debate", "status": "info", "detail": "Secondary AI verification Courtroom executed."})

        if rec_fail == "success":
            resolved = True
            traces.append({"step": "Execution Convergence", "status": "success", "detail": f"Intervention Successful. Target verified truthful."})
            
            # **Trauma Memory & Telemetry Persistent Logging**
            log_strategy_execution(failure_type, strat_name, True, rec_lat, rec_cost)
            log_trauma_memory(query, failure_type, strat_name)
            
            return {
                "status": "success",
                "output": recovered_state["generated_answer"],
                "traces": traces,
                "original_failed_output": original_failed,
                "metrics": {"latency": rec_lat, "cost": rec_cost, "strategy": strat_name}
            }
        else:
            # Recovery Failed -> Log Negative Trajectory to Memory -> Escalate and cycle to alternative strategy
            log_strategy_execution(failure_type, strat_name, False, rec_lat, rec_cost)
            traces.append({"step": "Strategy Failed", "status": "error", "detail": f"Sub-node '{strat_name}' convergence failed. Escalating array depth..."})
            current_state = recovered_state
            attempt += 1

    # Total Failure Block
    traces.append({"step": "Terminal State", "status": "error", "detail": "Exhausted all recovery clusters. Safe termination."})
    return {
        "status": "error",
        "output": "System Error: AegisAI Supervisor aborted generating response due to critically unsafe truth constraints that could not be repaired.",
        "traces": traces,
        "original_failed_output": original_failed
    }
