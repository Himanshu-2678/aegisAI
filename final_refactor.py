import os
import shutil

print("Executing final directory extraction...")

# Separate API routes from UI Presentation
if os.path.exists("api/templates"):
    os.makedirs("ui", exist_ok=True)
    shutil.move("api/templates", "ui/templates")
    print("Extracted UI from API.")

# Separate Query Optimizer logic out of generic agents
if os.path.exists("agent"):
    if os.path.exists("agent/query_optimizer.py"):
        shutil.move("agent/query_optimizer.py", "rag/optimizer.py")
        print("Moved optimizer to rag domain.")
    try: 
        os.rmdir("agent") # only if empty
        print("Deleted redundant agent/ directory.")
    except Exception as e:
        pass

# Fix internal file references
def replace_in_file(fp, old, new):
    if not os.path.exists(fp): return
    with open(fp, "r", encoding="utf-8") as f: c = f.read()
    if old in c:
        with open(fp, "w", encoding="utf-8") as f: f.write(c.replace(old, new))

replace_in_file("api/app.py", 'directory="api/templates"', 'directory="ui/templates"')
replace_in_file("rag/engine.py", "from agent.query_optimizer", "from rag.optimizer")

print("Cleanup complete.")
