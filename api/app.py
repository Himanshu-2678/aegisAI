import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from orchestrator.orchestrator import execute_with_supervisor

app = FastAPI(title="AegisAI Orchestrator")

# Ensure templates directory exists (handled by our setup script, but just in case)
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "templates")
templates = Jinja2Templates(directory=template_dir)

class QueryRequest(BaseModel):
    query: str
    inject_hallucination: bool = False
    inject_empty_context: bool = False
    enable_agentic_rewrite: bool = False
    enable_jury: bool = False

@app.get("/")
async def home(request: Request):
    response = templates.TemplateResponse(request=request, name="index.html")
    # Explicitly disable browser caching for rapid UI development!
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.post("/api/execute")
def execute_agent(req: QueryRequest):
    # This invokes our robust Supervisor Orchestrator.
    try:
        result = execute_with_supervisor(
            query=req.query,
            inject_hallucination=req.inject_hallucination,
            inject_empty_context=req.inject_empty_context,
            enable_agentic_rewrite=req.enable_agentic_rewrite,
            enable_jury=req.enable_jury
        )
        return result
    except Exception as e:
        return {"status": "error", "output": f"API Fatal Error: {str(e)}", "traces": [{"step": "API CRASH", "status": "error", "detail": str(e)}]}
