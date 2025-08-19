from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

# Import from your assistant.py
from assistant import (
    builder,  # Import the builder instead of compiled graph
    Analyst, 
    ResearchGraphState,
    MemorySaver
)

# Create graph with checkpointer for API
memory = MemorySaver()
graph = builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)

app = FastAPI(
    title="Research Assistant API",
    description="Multi-agent research system with human-in-the-loop feedback",
    version="1.0.0"
)

# Pydantic models for API
class ResearchRequest(BaseModel):
    topic: str
    max_analysts: int = 3

class AnalystFeedback(BaseModel):
    feedback: Optional[str] = None

class ResearchSession(BaseModel):
    session_id: str
    topic: str
    max_analysts: int
    status: str
    analysts: Optional[List[Dict[str, Any]]] = None
    final_report: Optional[str] = None
    created_at: datetime

# In-memory storage for sessions
sessions: Dict[str, Dict[str, Any]] = {}

@app.get("/", response_class=HTMLResponse)
async def root():
    """API documentation and test interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Research Assistant API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; }
            .post { background: #4CAF50; }
            .get { background: #2196F3; }
            .put { background: #FF9800; }
            pre { background: #f9f9f9; padding: 10px; border-radius: 3px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🔬 Research Assistant API</h1>
        <p>Multi-agent research system with human-in-the-loop feedback</p>
        
        <h2>Quick Start Guide:</h2>
        <ol>
            <li>Start a research session: <code>POST /research/start</code></li>
            <li>Review generated analysts: <code>GET /research/{session_id}/analysts</code></li>
            <li>Provide feedback (optional): <code>PUT /research/{session_id}/feedback</code></li>
            <li>Continue research: <code>POST /research/{session_id}/continue</code></li>
            <li>Get final report: <code>GET /research/{session_id}/report</code></li>
        </ol>

        <h2>API Endpoints:</h2>
        
        <div class="endpoint">
            <span class="method post">POST</span> <strong>/research/start</strong>
            <p>Start a new research session</p>
            <pre>{
  "topic": "The benefits of adopting LangGraph as an agent framework",
  "max_analysts": 3
}</pre>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span> <strong>/research/{session_id}/analysts</strong>
            <p>Get generated analysts for review</p>
        </div>

        <div class="endpoint">
            <span class="method put">PUT</span> <strong>/research/{session_id}/feedback</strong>
            <p>Provide feedback on analysts (optional)</p>
            <pre>{
  "feedback": "Add someone from a startup to add an entrepreneur perspective"
}</pre>
        </div>

        <div class="endpoint">
            <span class="method post">POST</span> <strong>/research/{session_id}/continue</strong>
            <p>Continue research process after feedback</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span> <strong>/research/{session_id}/report</strong>
            <p>Get the final research report</p>
        </div>

        <div class="endpoint">
            <span class="method get">GET</span> <strong>/research/sessions</strong>
            <p>List all research sessions</p>
        </div>

        <p><strong>Interactive API Docs:</strong> <a href="/docs">/docs</a> | <strong>ReDoc:</strong> <a href="/redoc">/redoc</a></p>
    </body>
    </html>
    """

@app.post("/research/start")
async def start_research(request: ResearchRequest):
    """Start a new research session and generate analysts"""
    session_id = str(uuid.uuid4())
    thread = {"configurable": {"thread_id": session_id}}
    
    try:
        # Run until first interruption (human feedback)
        events = list(graph.stream(
            {
                "topic": request.topic,
                "max_analysts": request.max_analysts
            },
            thread,
            stream_mode="values"
        ))
        
        # Get the analysts from the last event
        analysts = None
        for event in events:
            if 'analysts' in event:
                analysts = event['analysts']
        
        # Store session data
        sessions[session_id] = {
            "thread": thread,
            "topic": request.topic,
            "max_analysts": request.max_analysts,
            "status": "awaiting_feedback",
            "analysts": [analyst.dict() for analyst in analysts] if analysts else [],
            "created_at": datetime.now()
        }
        
        return {
            "session_id": session_id,
            "status": "awaiting_feedback",
            "message": "Analysts generated. Review them and provide feedback if needed.",
            "analysts": [analyst.dict() for analyst in analysts] if analysts else []
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting research: {str(e)}")

@app.get("/research/{session_id}/analysts")
async def get_analysts(session_id: str):
    """Get the generated analysts for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "topic": session["topic"],
        "analysts": session["analysts"],
        "status": session["status"]
    }

@app.put("/research/{session_id}/feedback")
async def provide_feedback(session_id: str, feedback: AnalystFeedback):
    """Provide feedback on the generated analysts"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    thread = session["thread"]
    
    try:
        # Update state with human feedback
        graph.update_state(
            thread, 
            {"human_analyst_feedback": feedback.feedback}, 
            as_node="human_feedback"
        )
        
        if feedback.feedback:
            # If feedback provided, regenerate analysts
            events = list(graph.stream(None, thread, stream_mode="values"))
            
            # Get updated analysts
            analysts = None
            for event in events:
                if 'analysts' in event:
                    analysts = event['analysts']
            
            # Update session
            sessions[session_id]["analysts"] = [analyst.dict() for analyst in analysts] if analysts else []
            sessions[session_id]["status"] = "feedback_incorporated"
            
            return {
                "message": "Feedback incorporated. New analysts generated.",
                "analysts": [analyst.dict() for analyst in analysts] if analysts else []
            }
        else:
            # No feedback, ready to continue
            sessions[session_id]["status"] = "ready_to_continue"
            return {
                "message": "No feedback provided. Ready to continue research.",
                "analysts": session["analysts"]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")

@app.post("/research/{session_id}/continue")
async def continue_research(session_id: str):
    """Continue the research process and generate the final report"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    thread = session["thread"]
    
    try:
        # If we haven't provided feedback yet, do it now with None
        if session["status"] == "awaiting_feedback":
            graph.update_state(
                thread, 
                {"human_analyst_feedback": None}, 
                as_node="human_feedback"
            )
        
        # Continue execution
        sessions[session_id]["status"] = "processing"
        
        events = list(graph.stream(None, thread, stream_mode="updates"))
        
        # Get final state
        final_state = graph.get_state(thread)
        final_report = final_state.values.get('final_report')
        
        # Update session
        sessions[session_id]["final_report"] = final_report
        sessions[session_id]["status"] = "completed"
        
        return {
            "session_id": session_id,
            "status": "completed",
            "message": "Research completed successfully!",
            "report_available": True
        }
        
    except Exception as e:
        sessions[session_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"Error continuing research: {str(e)}")

@app.get("/research/{session_id}/report")
async def get_report(session_id: str):
    """Get the final research report"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] != "completed":
        raise HTTPException(status_code=400, detail="Research not completed yet")
    
    if not session.get("final_report"):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "session_id": session_id,
        "topic": session["topic"],
        "report": session["final_report"],
        "created_at": session["created_at"]
    }

@app.get("/research/sessions")
async def list_sessions():
    """List all research sessions"""
    session_list = []
    for session_id, session_data in sessions.items():
        session_list.append({
            "session_id": session_id,
            "topic": session_data["topic"],
            "status": session_data["status"],
            "created_at": session_data["created_at"],
            "analysts_count": len(session_data.get("analysts", []))
        })
    
    return {"sessions": session_list}

@app.get("/research/{session_id}/status")
async def get_session_status(session_id: str):
    """Get the current status of a research session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return {
        "session_id": session_id,
        "status": session["status"],
        "topic": session["topic"],
        "created_at": session["created_at"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)