from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio
from threading import Thread
import time

# Import from your assistant.py
from assistant import (
    # For analyst generation part
    StateGraph, GenerateAnalystsState, create_analysts, human_feedback, should_continue,
    MemorySaver, Analyst, END, START,
    # For interview part  
    # interview_graph,
    interview_builder,
    # Other imports
    model, read_prompt_file
)

# Create the analyst generation graph
def create_analyst_graph():
    builder = StateGraph(GenerateAnalystsState)
    builder.add_node("create_analysts", create_analysts)
    builder.add_node("human_feedback", human_feedback)
    builder.add_edge(START, "create_analysts")
    builder.add_edge("create_analysts", "human_feedback")
    builder.add_conditional_edges("human_feedback", should_continue, ["create_analysts", END])
    memory = MemorySaver()
    return builder.compile(interrupt_before=['human_feedback'], checkpointer=memory)

# Create graphs
analyst_graph = create_analyst_graph()
memory = MemorySaver()

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
            .progress { background: #e0e0e0; border-radius: 10px; padding: 3px; margin: 10px 0; }
            .progress-bar { background: #4CAF50; height: 20px; border-radius: 8px; transition: width 0.3s; }
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
            <li>Check progress: <code>GET /research/{session_id}/progress</code></li>
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
            <span class="method get">GET</span> <strong>/research/{session_id}/progress</strong>
            <p>Get real-time progress of research</p>
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
        events = list(analyst_graph.stream(
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
            "created_at": datetime.now(),
            "progress": {
                "current_step": "analysts_generated",
                "completed_analysts": 0,
                "total_analysts": len(analysts) if analysts else 0,
                "current_analyst": None,
                "interviews": {},
                "sections": []
            }
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
        analyst_graph.update_state(
            thread, 
            {"human_analyst_feedback": feedback.feedback}, 
            as_node="human_feedback"
        )
        
        if feedback.feedback:
            # If feedback provided, regenerate analysts
            events = list(analyst_graph.stream(None, thread, stream_mode="values"))
            
            # Get updated analysts
            analysts = None
            for event in events:
                if 'analysts' in event:
                    analysts = event['analysts']
            
            # Update session
            sessions[session_id]["analysts"] = [analyst.dict() for analyst in analysts] if analysts else []
            sessions[session_id]["status"] = "feedback_incorporated"
            sessions[session_id]["progress"]["total_analysts"] = len(analysts) if analysts else 0
            
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

def run_interviews_with_progress(session_id: str, analysts: List[Analyst], topic: str):
    """Run interviews for all analysts and update progress"""
    try:
        sessions[session_id]["status"] = "conducting_interviews"
        sessions[session_id]["progress"]["current_step"] = "conducting_interviews"
        
        interviews_results = []
        sections = []
        
        for i, analyst in enumerate(analysts):
            # Update progress
            sessions[session_id]["progress"]["current_analyst"] = analyst.dict()
            sessions[session_id]["progress"]["completed_analysts"] = i
            
            try:
                # Create interview thread
                interview_thread = {"configurable": {"thread_id": f"{session_id}_analyst_{i}"}}
                
                # Set up initial message
                from langchain_core.messages import HumanMessage
                messages = [HumanMessage(f"So you said you were writing an article on {topic}?")]
                interview_graph = interview_builder.compile(checkpointer=memory).with_config(run_name="Conduct Interviews")
                # Run interview
                interview_result = interview_graph.invoke({
                    "analyst": analyst, 
                    "messages": messages, 
                    "max_num_turns": 2
                }, interview_thread)
                
                interviews_results.append(interview_result)
                
                # Store interview progress
                sessions[session_id]["progress"]["interviews"][analyst.name] = {
                    "status": "completed",
                    "interview": interview_result.get("interview", ""),
                    "section": interview_result.get("sections", [""])[0] if interview_result.get("sections") else ""
                }
                
                # Collect sections
                if interview_result.get("sections"):
                    sections.extend(interview_result["sections"])
                    sessions[session_id]["progress"]["sections"] = sections
                
            except Exception as e:
                sessions[session_id]["progress"]["interviews"][analyst.name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Update final progress
        sessions[session_id]["progress"]["completed_analysts"] = len(analysts)
        sessions[session_id]["progress"]["current_step"] = "generating_report"
        
        # Generate final report
        final_report = generate_final_report(topic, sections)
        sessions[session_id]["final_report"] = final_report
        sessions[session_id]["status"] = "completed"
        sessions[session_id]["progress"]["current_step"] = "completed"
        
    except Exception as e:
        sessions[session_id]["status"] = "error"
        sessions[session_id]["error"] = str(e)

def generate_final_report(topic: str, sections: List[str]) -> str:
    """Generate final report from sections"""
    try:
        # Use your model to generate a consolidated report
        from langchain_core.messages import SystemMessage, HumanMessage
        
        system_prompt = f"""You are a research report writer. You have been provided with research sections on the topic: {topic}

Your task is to synthesize these sections into a comprehensive, well-structured final report. 
- Create a coherent narrative that flows well
- Remove duplicate information
- Organize the content logically
- Add an executive summary at the beginning
- Include a conclusion at the end
- Use proper markdown formatting with headers and subheaders"""

        sections_text = "\n\n---\n\n".join(sections)
        
        final_report = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Here are the research sections:\n\n{sections_text}\n\nPlease create a comprehensive final report.")
        ])
        
        return final_report.content
        
    except Exception as e:
        return f"# Research Report: {topic}\n\n## Error\nFailed to generate final report: {str(e)}\n\n## Raw Sections\n\n" + "\n\n---\n\n".join(sections)

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
            analyst_graph.update_state(
                thread, 
                {"human_analyst_feedback": None}, 
                as_node="human_feedback"
            )
        
        # Get analysts
        analysts = [Analyst(**analyst_data) for analyst_data in session["analysts"]]
        topic = session["topic"]
        
        # Start interviews in background thread
        interview_thread = Thread(
            target=run_interviews_with_progress, 
            args=(session_id, analysts, topic)
        )
        interview_thread.start()
        
        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Research process started. Check progress endpoint for updates.",
            "total_analysts": len(analysts)
        }
        
    except Exception as e:
        sessions[session_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"Error continuing research: {str(e)}")

@app.get("/research/{session_id}/progress")
async def get_progress(session_id: str):
    """Get real-time progress of the research process"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    progress = session.get("progress", {})
    
    # Calculate progress percentage
    total_analysts = progress.get("total_analysts", 0)
    completed_analysts = progress.get("completed_analysts", 0)
    
    progress_percentage = 0
    if total_analysts > 0:
        if progress.get("current_step") == "completed":
            progress_percentage = 100
        elif progress.get("current_step") == "generating_report":
            progress_percentage = 90
        else:
            progress_percentage = min(90, (completed_analysts / total_analysts) * 80)
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "progress_percentage": progress_percentage,
        "current_step": progress.get("current_step", "unknown"),
        "completed_analysts": completed_analysts,
        "total_analysts": total_analysts,
        "current_analyst": progress.get("current_analyst"),
        "interviews": progress.get("interviews", {}),
        "sections_count": len(progress.get("sections", []))
    }

@app.get("/research/{session_id}/report")
async def get_report(session_id: str):
    """Get the final research report"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if session["status"] not in ["completed"]:
        raise HTTPException(status_code=400, detail=f"Research not completed yet. Current status: {session['status']}")
    
    if not session.get("final_report"):
        # Try to generate report from sections if available
        sections = session.get("progress", {}).get("sections", [])
        if sections:
            final_report = generate_final_report(session["topic"], sections)
            session["final_report"] = final_report
        else:
            raise HTTPException(status_code=404, detail="Report not found and no sections available")
    
    return {
        "session_id": session_id,
        "topic": session["topic"],
        "report": session["final_report"],
        "created_at": session["created_at"],
        "analysts_used": len(session.get("analysts", []))
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