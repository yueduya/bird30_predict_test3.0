from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import json

from auth.dependencies import get_current_user
from database.mongodb import save_message, get_recent_conversations, get_user_sessions, delete_session
from services.llm_service import chat_with_history_stream

router = APIRouter(prefix="/chat", tags=["聊天"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/send")
async def send_message(data: ChatRequest, user = Depends(get_current_user)):
    user_uuid = user["uuid"]
    session_id = data.session_id or str(uuid.uuid4())
    
    history = get_recent_conversations(user_uuid, n_rounds=10, session_id=session_id)
    
    save_message(user_uuid, "user", data.message, session_id)
    
    async def generate():
        full_reply = ""
        try:
            async for chunk in chat_with_history_stream(
                user_message=data.message,
                history=history
            ):
                full_reply += chunk
                yield f"data: {json.dumps({'content': chunk, 'session_id': session_id}, ensure_ascii=False)}\n\n"
            
            save_message(user_uuid, "assistant", full_reply, session_id)
            yield f"data: {json.dumps({'done': True, 'session_id': session_id}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/history")
async def get_history(session_id: str = None, user = Depends(get_current_user)):
    history = get_recent_conversations(
        user["uuid"], 
        n_rounds=50, 
        session_id=session_id
    )
    return {"success": True, "data": history}

@router.get("/sessions")
async def get_sessions(user = Depends(get_current_user)):
    sessions = get_user_sessions(user["uuid"])
    return {"success": True, "data": sessions}

@router.delete("/session/{session_id}")
async def remove_session(session_id: str, user = Depends(get_current_user)):
    delete_session(user["uuid"], session_id)
    return {"success": True, "message": "会话已删除"}
