import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from orchestrator.orchestrator import execute_with_supervisor
import json
import threading
import queue

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
    # Streaming Real-Time Telemetry Pipeline via background Thread & NDJSON Queue
    q = queue.Queue()

    def on_trace(t):
        q.put({"event": "trace", "data": t})

    def worker():
        try:
            result = execute_with_supervisor(
                query=req.query,
                inject_hallucination=req.inject_hallucination,
                inject_empty_context=req.inject_empty_context,
                enable_agentic_rewrite=req.enable_agentic_rewrite,
                enable_jury=req.enable_jury,
                on_trace=on_trace
            )
            q.put({"event": "final", "data": result})
        except Exception as e:
            q.put({"event": "error", "data": {"step": "API CRASH", "status": "error", "detail": str(e)}})
        finally:
            q.put(None)

    threading.Thread(target=worker).start()

    def stream_generator():
        while True:
            item = q.get()
            if item is None:
                break
            yield json.dumps(item) + "\n"

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
