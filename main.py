from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
import uvicorn
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from dotenv import load_dotenv
load_dotenv()

import os
from google.genai import Client

# Configure the client - this sets up authentication globally
Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- Agent setup ----------------------------------------------------------
def get_weather(city: str) -> str:
    """Gets the current weather for a city.
    Args:
        city: The name of the city to get weather for.
    Returns:
        A string with the weather description.
    """
    return f"The weather in {city} is sunny."

agent = LlmAgent(
    name="api_agent",
    model="gemini-2.0-flash",
    tools=[get_weather],
    description="A helpful assistant that can check weather."
)

session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name="api_app",
    session_service=session_service
    
)

# --- Request/Response models ----------------------------------------------
class QueryRequest(BaseModel):
    query: str
    session_id: str = None
    user_id: str = None
class QueryResponse(BaseModel):
    user_id: str
    session_id: str
    response: str
    
# --- FastAPI app ----------------------------------------------------------
app = FastAPI(title="ADK Agent API")
@app.post("/query", response_model=QueryResponse)
async def query_agent(req: QueryRequest):
    # generate IDs if missing
    
    print("inside the api")
    user_id = req.user_id or f"user_{uuid.uuid4().hex[:8]}"
    session_id = req.session_id or f"session_{uuid.uuid4().hex[:8]}"
    # ensure session exists
    if await session_service.get_session(app_name="api_app", user_id=user_id, session_id= session_id) is None:
        print('creating a session for', session_id)
        await session_service.create_session(app_name="api_app", user_id=user_id, session_id= session_id)
        
    print("after session")
    
    # build message
    content = types.Content(
        role="user",
        parts=[types.Part(text=req.query)]
    )
    
    print("after content")
    
    # stream until final and grab the text
    response_text = None
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            
    return QueryResponse(
        user_id=user_id,
        session_id=session_id,
        response=response_text or ""
    )
    
    
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()
    # each WS connection gets its own user_id
    user_id = f"ws_user_{uuid.uuid4().hex[:8]}"
    # ensure session exists
    if session_service.get_session(app_name="api_app", user_id=user_id, session_id= session_id is None):
        session_service.create_session(app_name="api_app", user_id=user_id, session_id= session_id)
    # let client know its user_id
    await ws.send_json({"type": "session_init", "user_id": user_id, "session_id": session_id})
    try:
        while True:
            query = await ws.receive_text()
            content = types.Content(
                role="user",
                parts=[types.Part(text=query)]
            )
            # stream all events, pushing each as JSON
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                payload = {
                    "type": "event",
                    "id": event.id,
                    "author": event.author,
                }
                if event.content and event.content.parts:
                    payload["text"] = event.content.parts[0].text
                if event.is_final_response():
                    payload["is_final"] = True
                await ws.send_json(payload)
    except WebSocketDisconnect:
        # client closed connection
        pass
    except Exception as e:
        # on error, close cleanly
        await ws.send_json({"type": "error", "message": str(e)})
        await ws.close()
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)