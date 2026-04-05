import os
import shutil

print("Starting deep architectural refactoring...")

# 1. Rename directories
if os.path.exists("supervisor"):
    os.rename("supervisor", "orchestrator")
    print("Renamed supervisor -> orchestrator")

if os.path.exists("demo"):
    os.rename("demo", "api")
    print("Renamed demo -> api")

# 2. Extract modules to correct domains
if not os.path.exists("security"): os.makedirs("security")
if os.path.exists("evaluation/firewall.py"):
    shutil.move("evaluation/firewall.py", "security/firewall.py")
    print("Decoupled firewall.py into security/ domain")

if not os.path.exists("rag"): os.makedirs("rag")
if os.path.exists("agent/rag.py"):
    shutil.move("agent/rag.py", "rag/engine.py")
    print("Decoupled rag.py backwards into dedicated rag/ domain")

# 3. Patch all hardcoded internal routing references
replacements = {
    "from supervisor.orchestrator": "from orchestrator.orchestrator",
    "from evaluation.firewall": "from security.firewall",
    "from agent.rag": "from rag.engine",
    "supervisor.orchestrator": "orchestrator.orchestrator",
    "evaluation.firewall": "security.firewall",
    "agent.rag": "rag.engine",
    "demo/templates": "api/templates",
    "demo.app:app": "api.app:app"
}

for root, dirs, files in os.walk("."):
    if "venv" in root or "__pycache__" in root or ".git" in root: continue
    for file in files:
        if file.endswith(".py") or file == "main.py" or file.endswith(".json") or file.endswith(".md"):
            if file == "refactor.py": continue
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            original = content
            for old, new in replacements.items():
                content = content.replace(old, new)
            if content != original:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Patched internal dependencies within: {filepath}")

print("Architecture rigidly refactored!")
