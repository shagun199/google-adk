from google.genai import Client
import os
from fastapi import FastAPI
from pydantic import BaseModel
import uuid
import uvicorn
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field
from firebase.firebase_functions import authenticateUser


from dotenv import load_dotenv
load_dotenv()


# Configure the client - this sets up authentication globally
Client(api_key=os.getenv("GOOGLE_API_KEY"))


# --- Agent setup ----------------------------------------------------------
agent = LlmAgent(
    name="general_agent",
    model="gemini-2.0-flash",
    description="A helpful assistant that can answer any question or provide information.",
    instruction="""You are a helpful assistant that answers any question or provides useful information. 
Always respond clearly, politely, and helpfully. If you don't know the answer, say so honestly and suggest where to find more information."""
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
    phone_number: str = None


class QueryResponse(BaseModel):
    user_id: str
    session_id: str
    response: str


# --- FastAPI app ----------------------------------------------------------
app = FastAPI(title="ADK Agent API")


@app.post("/query", response_model=QueryResponse)
async def query_agent(req: QueryRequest):
    phone_number = req.phone_number
    print(f"phone_number entered by user : {phone_number}")

    user_id = await authenticateUser(phone_number)
    print(f"user_id from firebase : {user_id}")

    session_id = req.session_id or f"session_{uuid.uuid4().hex[:8]}"
    # ensure session exists
    if await session_service.get_session(app_name="api_app", user_id=user_id, session_id=session_id) is None:
        print('creating a session for', session_id)
        await session_service.create_session(app_name="api_app", user_id=user_id, session_id=session_id)

    # build message
    content = types.Content(
        role="user",
        parts=[types.Part(text=req.query)]
    )
    
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
