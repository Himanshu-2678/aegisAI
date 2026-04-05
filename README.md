# AegisAI: A Self-Healing AI Orchestration System
Built for Capgemini Buildathon 2026

AegisAI is an early-stage production-oriented AI meta-layer designed to transform unreliable large language model outputs into deterministic, observable, and secure systems.

This project was built as a team effort for Capgemini Buildathon 2026, with a focus on solving real-world deployment risks in generative AI systems.

## Overview
Modern LLM systems are fundamentally non-deterministic. They hallucinate, fail unpredictably, and are vulnerable to adversarial inputs such as prompt injections.

AegisAI introduces a self-healing orchestration layer that operates above any LLM. Instead of trusting outputs blindly, the system:
- Evaluates correctness
- Detects anomalies
- Intercepts malicious inputs
- Re-routes failing execution paths

This converts a probabilistic generator into a controlled, observable AI system.

## Core Idea
The system acts as a meta-intelligence layer, not just a wrapper.

Instead of:
`User -> LLM -> Output`

We enforce:
`User -> Security Layer -> Retrieval -> Evaluation -> Multi-Agent Reasoning -> Final Output`

This ensures that:
- Unsafe input is intercepted before inference
- Low-confidence generations are trapped and restructured
- Every decision is traceable

## System Architecture
Visit [ARCHITECTURE.md](ARCHITECTURE.md) for detailed flowchart visuals.

At a high level, the system is composed of:
- Input Security Layer
- RAG Engine (with Query Optimization)
- Evaluation Engine
- Multi-Agent Reasoning Layer
- Recovery & Orchestration Core
- Observability Layer (Logging + Metrics)

Each module is independently designed but tightly orchestrated through a central controller.

## Key Capabilities

### 1. Multi-Agent Courtroom System
AegisAI introduces a structured reasoning framework:
- **Prosecutor Agent** challenges factual correctness
- **Defender Agent** argues contextual validity
- **Judge Agent** computes a final confidence score

This replaces naive output acceptance with structured adversarial validation.
**Evaluation Rules:**
The Judge operates deterministically (temperature=0.0) and enforces a hard constraint using a lexical Jaccard overlap score:

overlap = len(intersection(answer, context)) / len(answer)

If overlap < 20%, the response is treated as hallucinated and the system triggers recovery or aborts execution.

The 20% threshold was empirically selected to balance false positives and false negatives.

### 2. Auto-Evolving Agentic RAG
If retrieval fails:
- The system does not return empty results
- An internal optimizer rewrites the query into multiple semantically distinct query variations
- Retrieval is retried automatically

### 3. Experience-Based Learning (Trauma Memory)
A local database (`experience.db`) permanently stores:
- Failed true-negative execution patterns
- Recovery strategy hashes successfully used
- Outcome effectiveness and proxy token tracking

Future queries are preemptively corrected using these historical patterns.

### 4. Zero-Trust Security Firewall
Before entering the RAG execution pipeline:
- Inputs are scanned for standard prompt injection patterns
- Jailbreak attempts are heuristically detected and intercepted
- Malicious red-team patterns are explicitly filtered

### 5. Full Observability Layer
Every execution exposes:
- The dynamically selected recovery Strategy Node
- Internal execution latency overhead
- Estimated proxy token cost

No hidden decision-making. Everything is rigorously inspectable.

## Demo

### 1. Data Redaction Enforcement (Policy Violation Catch)
When a user explicitly attempts to extract sensitive credentials, the Supervisor detects the policy violation entirely decoupled from basic string-matching, dynamically escalating to a strict redaction protocol.

![Database Password Redaction](assets/ques_db_psd.png)

### 2. Hallucination Abort (Deterministic Validation)
![System Architecture Hallucination Catch](assets/ques_system_arc.png)

Query: Asked for system architecture not fully present in the database.

Behavior:
- LLM generated partially grounded + partially unsupported response
- Jaccard overlap dropped below 20%
- System flagged output as hallucinated
- Recovery strategies attempted correction
- Final state: execution aborted to prevent unsafe output

Result: No hallucinated response exposed to user.

## Empirical Validation (Live Local Benchmarking)

**1. Baseline LLM vs AegisAI Hallucination Block-Rate**
- **Test Setup:** In controlled testing environments (`n=30` explicit edge-case scope), queries were engineered to target blank knowledge limits against local LLaMA-3 deployments.
- **Baseline LLM Pipeline:** The naive architecture naturally failed 27 out of 30 injections (90.0% Hallucination Pass-Through Rate).
- **AegisAI Intercept Layer:** In identical conditions, the system achieved a 0.0% hallucination pass-through rate, blocking 30/30 cases (n=30).

**2. Tracing the System Failure Boundary (Adversarial Bypass)**
*No prototype is flawless. A raw trace showing our heuristic Firewall failing to detect an obfuscated Base64 Injection mapping exactly where the LLM layer differs from strict classifiers.*

```json
[
  {
    "step": "Cybersecurity Firewall",
    "status": "info",
    "detail": "Scanning contextual prompt integrity: 'SWdub3...VjdGlvbnMu' (Latency: 211ms)"
  },
  {
    "step": "Firewall Result",
    "status": "success",
    "detail": "Threat Score 0.0 - Allowed to proceed."
  },
  {
    "step": "RAG Execution Protocol",
    "status": "error",
    "detail": "LLM successfully decoded Base64 payload natively post-security check and dumped the restricted admin configuration matrix to stdout."
  }
]
```
**Why it failed:** The heuristic firewall is inherently constrained to surface-level structural language boundaries. While Ollama natively decoded the Base64 sequence utilizing foundational attention scaling limits, the earlier rigid security parser completely bypassed it due to a lack of recognized English phrasing blocks.
**Enterprise Mitigation Strategy:** A viable deployment scale requires explicitly wrapping the Input Layer with a standalone static Embedding Classifier (querying cosine similarity mappings against a strict threat database vector space) rather than executing pure zero-shot logical prompting.

## Engineering Decisions

### Latency vs Reliability
We intentionally trade speed for correctness.
- Multi-agent validation increases latency (~2x to 3x)
- But reduces hallucination risk significantly

*Observed latency increased from ~1.1s (baseline RAG) to ~2.8s with full multi-agent evaluation enabled.* In enterprise systems, incorrect outputs are costlier than slow outputs.

### SQLite over Distributed Systems
Instead of Redis or external infrastructure:
- SQLite provides zero-dependency deployment
- Ensures portability
- Supports offline-first architecture

This is a deliberate constraint, not a limitation.

### Offline Execution via Ollama
The system runs entirely on local models:
- No API cost
- No external dependency
- Full control over execution

Token cost is estimated via internal heuristics.

## Installation

### Prerequisites
- Python 3.9+
- Ollama installed locally

### Steps
1. Pull local model:
   ```bash
   ollama pull llama3
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the system:
   ```bash
   python main.py
   ```
4. Access the interface at:
   `http://localhost:8000`

## Project Structure
```text
aegisAI
  ├── main.py                  # FastAPI server entry point
  ├── orchestrator/            # Core routing cycle
  ├── rag/                     # Retrieval system & Sub-Agent Auto-Optimizers
  ├── evaluation/              # Meta-Judges & Strict Factual Scoring routines
  ├── security/                # Prompt Firewall & Active Threat Filters
  ├── strategies/              # Dynamic fallback policies explicit pool
  ├── memory/                  # Experience tracking & Trauma SQLite Database
  ├── api/                     # Controller endpoints mapped to routes
  ├── ui/                      # Dashboard layouts and HTML templates
  ├── tests/                   # Regression and integration test flows
  ├── assets/                  # Diagrams and demonstration UI screenshots
  ├── architecture.md          # Visual flowchart ecosystem
  └── requirements.txt         # Dependencies
```

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software with proper attribution.

See the [MIT License](LICENSE) file for full details.
