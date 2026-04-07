# AegisAI Architecture

This document outlines the high-level architecture of AegisAI, a self-healing AI orchestration system designed to enforce deterministic validation and security over LLM pipelines.

## Architecture Diagram

![AegisAI Architecture](assets/architecture_diagram_aegisAI.png)

## Flow Overview

1. **User Input**
   - Incoming query enters the system

2. **Master Security Firewall**
   - Detects prompt injection, credential harvesting, and explicitly blocks malicious requests via rule-based intercepts.

3. **Multi-Intent Decomposition**
   - Heuristically detects compound queries.
   - Strictly splits independent intents via enforced JSON outputs.

4. **Policy Routing Array**
   - **Sensitive Path:** Instantly terminates and flags execution.
   - **General Path:** Fast-tracks world-knowledge queries, constrained by structural ignorance guardrails (softening outputs).
   - **Grounded Path:** Locks queries to internal vectors, moving to the RAG Layer.

5. **RAG & Evaluation Layer (Grounded Only)**
   - Retrieves relevant context.
   - Applies deterministic Jaccard scoring (< 20% rejected).
   - Multi-agent courtroom evaluates factual boundaries.
   - Invokes automatic recovery or aborts dynamically.

6. **Rule-Based Fusion Output**
   - Combines validated sub-queries dynamically via immutable Python formatting.
   - Prevents General outputs from hallucinating or overwriting Grounded facts.
   - Safe, validated response returned to user dynamically streamed via NDJSON.

## Key Property

The system enforces a hard constraint:
- If lexical overlap < 20% → response is rejected or corrected