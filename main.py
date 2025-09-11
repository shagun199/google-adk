import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from google.genai import Client
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from firebase.firebase_functions import authenticateUser

from helpers.utils import get_or_create_session, process_query

# --- Load environment variables ---
load_dotenv()

# Configure the client - this sets up authentication globally
Client(api_key=os.getenv("GOOGLE_API_KEY"))


# --- Agent setup ----------------------------------------------------------
# agent = LlmAgent(
#     name="general_agent",
#     model="gemini-2.0-flash",
#     description="A helpful assistant that can answer any question or provide information.",
#     instruction="""You are a helpful assistant that answers any question or provides useful information.
# Always respond clearly, politely, and helpfully. If you don't know the answer, say so honestly and suggest where to find more information."""
# )

# booking_agent = LlmAgent(
#     name="Booker",
#     description="Handles flight and hotel bookings."
# )

# info_agent = LlmAgent(
#     name="Info",
#     description="Provides general information and answers questions."
# )

# coordinator = LlmAgent(
#     name="Coordinator",
#     model="gemini-2.0-flash",
#     instruction="You are an assistant. Delegate booking tasks to Booker and info requests to Info.",
#     description="Main coordinator.",
#     # AutoFlow is typically used implicitly here
#     sub_agents=[booking_agent, info_agent]
# )

validator = LlmAgent(
    name="ValidateInput", 
    instruction="Validate the input.",
    output_key="validation_status",
    model="gemini-2.0-flash"
)

processor = LlmAgent(
    name="ProcessData",
    instruction="Process data if {validation_status} is 'valid'.",
    output_key="result",
    model="gemini-2.0-flash"
)

reporter = LlmAgent(
    name="ReportResult",
    instruction="Report the result from {result}.",
    model="gemini-2.0-flash"
)

data_pipeline = SequentialAgent(
    name="DataPipeline",
    sub_agents=[validator, processor, reporter]
)

session_service = InMemorySessionService()
runner = Runner(
    agent=data_pipeline,
    app_name="coordinator",
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
    print(f"Phone number: {phone_number}")

    user_id = await authenticateUser(phone_number)
    print(f"Authenticated user_id: {user_id}")

    session_id = req.session_id or f"session_{uuid.uuid4().hex[:8]}"
    session_id = await get_or_create_session(session_service, user_id, session_id)

    response_text = await process_query(runner, user_id, session_id, req.query)

    return QueryResponse(user_id=user_id, session_id=session_id, response=response_text or "No response from agent.")


# --- Run app ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
