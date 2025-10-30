"""CLO Companion API - FastAPI server for garment generation and editing"""

import os
import sys
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from logger import log
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")

from modules.clo_companion.garment_gen import GarmentGenerator
from modules.clo_companion.feedback_interpreter import FeedbackInterpreter
from modules.clo_companion.garment_editor import GarmentEditor
from modules.clo_companion.design_state import DesignStateTracker
from modules.clo_companion.mode_manager import get_mode_manager
from modules.clo_companion.prompt_router import get_prompt_router
from modules.clo_companion.intent_classifier import get_intent_classifier
from modules.clo_companion.render_manager import RenderManager
from modules.clo_companion.gpu_monitor import GPUMonitor

app = FastAPI(title="CLO Companion API", version="7.0.0")

# Initialize components
interpreter = FeedbackInterpreter()
editor = GarmentEditor()
state_tracker = DesignStateTracker()
mode_manager = get_mode_manager()
prompt_router = get_prompt_router()
intent_classifier = get_intent_classifier()
render_manager = RenderManager()
gpu_monitor = GPUMonitor()

# Initialize generator
generator = GarmentGenerator()

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    seed: Optional[int] = None

class GenerateResponse(BaseModel):
    status: str
    obj_file: str
    mtl_file: Optional[str] = None
    metadata_file: Optional[str] = None
    preview_file: Optional[str] = None
    base_name: str
    message: str
    timestamp: str = None

class IterateRequest(BaseModel):
    feedback: str

class IterateResponse(BaseModel):
    status: str
    obj_file: str
    mtl_file: Optional[str] = None
    metadata_file: Optional[str] = None
    preview_file: Optional[str] = None
    base_name: str
    version: int
    message: str
    mode: Optional[str] = None  # Added for autorouter

class ChatMessageRequest(BaseModel):
    message: str
    role: str = "user"  # "user" or "ai"

# CORS configuration (localhost only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:*", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CLO Companion API",
        "version": "6.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CLO Companion API",
        "version": "6.0.0",
        "output_dir": generator.output_dir,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/generate_garment", response_model=GenerateResponse)
async def generate_garment(request: GenerateRequest):
    """
    Generate garment from text prompt
    
    Example prompts:
    - "white cotton t-shirt with rolled sleeves"
    - "oversized beige trench coat with belt"
    - "black denim pants"
    """
    try:
        log(f"Generating garment from prompt: {request.prompt}", "CLO")
        
        result = generator.generate(
            prompt=request.prompt,
            seed=request.seed
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Generation failed")
        
        # Update design state
        state_tracker.update_state(
            current_file=os.path.basename(result["obj_file"]),
            prompt=request.prompt,
            attributes=result.get("attributes", {}),
            version=1
        )
        
        # Add to chat history
        state_tracker.add_chat_message("user", request.prompt)
        state_tracker.add_chat_message("ai", f"✅ Generated: {result.get('base_name', 'unknown')}")
        
        return GenerateResponse(
            status="success",
            obj_file=os.path.basename(result["obj_file"]),
            mtl_file=os.path.basename(result.get("mtl_file", "")),
            metadata_file=os.path.basename(result.get("metadata_file", "")),
            preview_file=os.path.basename(result["preview_file"]) if result.get("preview_file") and os.path.exists(result["preview_file"]) else None,
            base_name=result.get("base_name", ""),
            message=f"Garment generated successfully",
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"Error generating garment: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/iterate", response_model=IterateResponse)
async def iterate_design(request: IterateRequest):
    """
    Iterate on existing design based on feedback
    
    Auto-detects intent and routes to EDIT mode if needed
    """
    try:
        # Auto-detect intent using intent classifier
        intent, confidence = intent_classifier.detect_intent(request.feedback)
        
        log(f"Feedback received (intent: {intent}, confidence: {confidence:.2f}): {request.feedback}", "CLO")
        
        # Get current state
        state = state_tracker.get_current_state()
        current_file = state.get("current_file")
        
        if not current_file:
            raise HTTPException(status_code=400, detail="No active design. Generate a garment first.")
        
        # Find full path
        obj_file = os.path.join(generator.output_dir, current_file)
        if not os.path.exists(obj_file):
            # Try without extension
            obj_file = os.path.join(generator.output_dir, current_file.replace(".obj", "") + ".obj")
            if not os.path.exists(obj_file):
                raise HTTPException(status_code=404, detail=f"Design file not found: {current_file}")
        
        # Get design context and chat history
        design_context = state_tracker.get_design_context()
        chat_history = state_tracker.get_chat_history(limit=6)  # Last 6 messages
        
        # Build context using prompt router
        if prompt_router:
            context_str = prompt_router.build_context(
                "CLO_WIZARD" if intent == "EDIT" else "CHAT",
                state,
                chat_history
            )
        else:
            context_str = ""
        
        # Interpret feedback (will use detected intent for mode)
        context = {
            "current_file": current_file,
            "attributes": state.get("attributes", {}),
            "last_prompt": state.get("last_prompt", "")
        }
        
        # Set mode based on intent
        if intent == "EDIT":
            detected_mode = "CLO_WIZARD"
        else:
            detected_mode = "CHAT"
        
        if mode_manager:
            mode_manager.set_mode(detected_mode, f"Auto-routed from intent: {intent}")
        
        interpretation = interpreter.interpret(request.feedback, context)
        
        # Check if this is a new generation request
        if interpretation.get("is_new_generation", False):
            # Fall back to new generation
            log("Feedback interpreted as new generation, generating from scratch", "CLO")
            gen_request = GenerateRequest(prompt=interpretation.get("value", request.feedback))
            return await generate_garment(gen_request)
        
        # Get version number
        current_version = state.get("version", 1)
        new_version = current_version + 1
        
        # Get edit commands
        commands = interpretation.get("commands", [])
        if not commands:
            commands = [{"action": interpretation.get("action", "adjust_fit"), 
                       "value": interpretation.get("value", request.feedback)}]
        
        # Apply edits (only if EDIT intent)
        if intent == "EDIT":
            result = editor.apply_edit(
                model_path=obj_file,
                feedback_text=request.feedback,
                edit_commands=commands,
                version=new_version
            )
            
            if not result:
                raise HTTPException(status_code=500, detail="Failed to apply edits")
            
            # Update state
            state_tracker.update_state(
                current_file=os.path.basename(result["obj_file"]),
                prompt=state.get("last_prompt", ""),
                attributes=state.get("attributes", {}),
                version=new_version
            )
            
            # Add to chat history with edit summary
            state_tracker.add_chat_message("user", request.feedback)
            edit_summary = f"Updated to v{new_version}: {result.get('base_name', 'unknown')}"
            state_tracker.add_chat_message("ai", f"✅ {edit_summary} — preview updated.")
            
            # Auto-return to CHAT mode after successful edit
            if mode_manager:
                mode_manager.return_to_chat("Command execution completed")
            
            return IterateResponse(
                status="success",
                obj_file=os.path.basename(result["obj_file"]),
                mtl_file=os.path.basename(result.get("mtl_file", "")),
                metadata_file=os.path.basename(result.get("metadata_file", "")),
                preview_file=os.path.basename(result["preview_file"]) if result.get("preview_file") and os.path.exists(result["preview_file"]) else None,
                base_name=result.get("base_name", ""),
                version=new_version,
                message=f"Design updated to v{new_version}",
                mode="EDIT"
            )
        else:
            # CHAT intent - return conversational response
            chat_response = f"I understand you're asking about: {request.feedback}. This appears to be a conversational query rather than a design modification."
            
            state_tracker.add_chat_message("user", request.feedback)
            state_tracker.add_chat_message("ai", chat_response)
            
            return IterateResponse(
                status="chat_response",
                obj_file=os.path.basename(current_file) if current_file else "",
                mtl_file=None,
                metadata_file=None,
                preview_file=None,
                base_name=state.get("last_prompt", "current_design"),
                version=state.get("version", 1),
                message=chat_response,
                mode="CHAT"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"Error iterating design: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat_history")
async def get_chat_history(limit: int = 50):
    """Get chat history"""
    try:
        history = state_tracker.get_chat_history(limit=limit)
        return {"status": "success", "history": history, "count": len(history)}
    except Exception as e:
        log(f"Error getting chat history: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat_message")
async def add_chat_message(request: ChatMessageRequest):
    """Add message to chat history"""
    try:
        state_tracker.add_chat_message(request.role, request.message)
        return {"status": "success", "message": "Chat message added"}
    except Exception as e:
        log(f"Error adding chat message: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/design_state")
async def get_design_state():
    """Get current design state"""
    try:
        state = state_tracker.get_current_state()
        return {"status": "success", "state": state}
    except Exception as e:
        log(f"Error getting design state: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/undo")
async def undo_last_change():
    """Undo last design change"""
    try:
        previous_file = state_tracker.get_previous_version()
        
        if not previous_file:
            raise HTTPException(status_code=400, detail="No previous version to undo")
        
        state = state_tracker.get_current_state()
        history = state.get("history", [])
        
        if len(history) < 2:
            raise HTTPException(status_code=400, detail="Cannot undo - only one version exists")
        
        # Find previous version
        current_file = state.get("current_file")
        prev_idx = len(history) - 2
        previous_file = history[prev_idx]
        
        # Update state to previous version
        state_tracker.update_state(
            current_file=previous_file,
            prompt=state.get("last_prompt", ""),
            attributes=state.get("attributes", {}),
            version=max(1, state.get("version", 1) - 1)
        )
        
        state_tracker.add_chat_message("user", "/undo")
        state_tracker.add_chat_message("ai", f"✅ Reverted to previous version: {os.path.basename(previous_file)}")
        
        return {
            "status": "success",
            "message": f"Reverted to previous version",
            "current_file": previous_file,
            "version": max(1, state.get("version", 1) - 1)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"Error undoing change: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/list_outputs")
async def list_outputs():
    """List all generated garments"""
    try:
        outputs = []
        output_dir = generator.output_dir
        
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith(".obj"):
                    file_path = os.path.join(output_dir, file)
                    metadata_file = file_path.replace(".obj", "_metadata.json")
                    
                    metadata = {}
                    if os.path.exists(metadata_file):
                        import json
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        except:
                            pass
                    
                    outputs.append({
                        "obj_file": file,
                        "prompt": metadata.get("prompt", "unknown"),
                        "timestamp": metadata.get("timestamp", ""),
                        "base_name": metadata.get("base_name", file.replace(".obj", ""))
                    })
        
        return {"status": "success", "outputs": outputs, "count": len(outputs)}
    except Exception as e:
        log(f"Error listing outputs: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preview/{file_id}")
async def get_preview(file_id: str):
    """Get preview image for a garment"""
    try:
        preview_path = os.path.join(generator.output_dir, "previews", f"{file_id}.png")
        
        if not os.path.exists(preview_path):
            raise HTTPException(status_code=404, detail="Preview not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(preview_path, media_type="image/png")
        
    except HTTPException:
        raise
    except Exception as e:
        log(f"Error getting preview: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect_intent")
async def detect_intent_endpoint(request: dict):
    """Detect intent for a text message (for UI preview)"""
    try:
        text = request.get("text", "")
        intent, confidence = intent_classifier.detect_intent(text)
        return {
            "intent": intent,
            "confidence": confidence,
            "mode": "CLO_WIZARD" if intent == "EDIT" else "CHAT"
        }
    except Exception as e:
        log(f"Error detecting intent: {e}", "CLO", level="ERROR")
        return {"intent": "CHAT", "confidence": 0.5, "mode": "CHAT"}

@app.post("/record_false_positive")
async def record_false_positive_endpoint(request: dict):
    """Record a false positive for intent classification"""
    try:
        text = request.get("text", "")
        detected = request.get("detected_intent", "")
        correct = request.get("correct_intent", "")
        
        intent_classifier.record_false_positive(text, detected, correct)
        
        return {"status": "success", "message": "False positive recorded"}
    except Exception as e:
        log(f"Error recording false positive: {e}", "CLO", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))
