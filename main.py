import os
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from google.genai import Client
from google.adk.agents import LlmAgent, SequentialAgent, Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from firebase.firebase_functions import authenticateUser

from helpers.utils import get_or_create_session, process_query
from toolbox_core import ToolboxSyncClient
from google.adk.tools.agent_tool import AgentTool

from agents.booking_management_agent.agent import booking_management_agent
from agents.car_rental_agent.agent import car_rental_agent
from agents.flights_agent.agent import flights_agent
from agents.hotels_agent.agent import hotels_agent
from agents.restaurants_agent.agent import restaurants_agent

# --- Load environment variables ---
load_dotenv()

# Configure the client - this sets up authentication globally
Client(api_key=os.getenv("GOOGLE_API_KEY"))
toolbox = ToolboxSyncClient("http://127.0.0.1:5000")
tools = toolbox.load_toolset('hotels_toolset')

# --- Agent setup ----------------------------------------------------------
booking_management_tool = AgentTool(booking_management_agent)
car_rental_tool = AgentTool(car_rental_agent)
flights_tool = AgentTool(flights_agent)
hotels_tool = AgentTool(hotels_agent)
restaurants_tool = AgentTool(restaurants_agent)

root_agent = Agent(
    name="travel_coordinator_agent",
    model="gemini-2.5-flash",
    description=(
        "Intelligent travel coordinator agent that analyzes user queries and routes them to the most appropriate specialized tools. "
        "This agent serves as the central hub for all travel-related requests including hotels, flights, restaurants, car rentals, and booking management. "
        "It understands natural language queries about travel planning, searches, and reservations, then delegates to the right specialist tools "
        "to provide comprehensive and accurate responses. The agent can handle single-service requests as well as complex multi-service travel planning scenarios."
    ),
    instruction=(
        """You are an expert Travel Coordinator Agent responsible for intelligently routing user queries to the most appropriate tools based on their travel needs.

**CORE RESPONSIBILITIES:**
1. **Query Analysis**: Carefully analyze each user query to identify the primary intent and required services
2. **Tool Selection**: Select the most appropriate tool(s) based on query keywords, context, and user intent
3. **Multi-Service Coordination**: Handle complex queries that may require multiple tools working together
4. **Response Synthesis**: Combine results from multiple tools into coherent, helpful responses

**ROUTING LOGIC BY QUERY TYPE:**

**HOTEL QUERIES** - Use `hotels_tools` when users ask about:
- Keywords: "hotel", "accommodation", "stay", "room", "lodge", "resort", "inn"
- Examples: "Find hotels in New York", "Show me luxury hotels", "What amenities does Hotel ABC have?"
- Actions: Search by name, location, price tier, or get amenity details

**FLIGHT QUERIES** - Use `flights_tools` when users ask about:
- Keywords: "flight", "airline", "fly", "plane", "airport", "ticket", "departure", "arrival"
- Examples: "Flights from NYC to LA", "American Airlines flights", "Available flights tomorrow"
- Actions: Search by route, airline, or check availability

**RESTAURANT QUERIES** - Use `restaurants_tools` when users ask about:
- Keywords: "restaurant", "food", "dining", "eat", "cuisine", "menu", "breakfast", "lunch", "dinner"
- Examples: "Italian restaurants in Chicago", "Show me the menu for Restaurant XYZ", "Best rated restaurants"
- Actions: Search by cuisine type, location, or get menu information

**CAR RENTAL QUERIES** - Use `car_rental_tools` when users ask about:
- Keywords: "car", "rental", "rent", "drive", "vehicle", "pickup", "SUV", "sedan", "economy"
- Examples: "Rent a car in Miami", "Available SUVs", "Car rental at airport"
- Actions: Search by location, vehicle type, or check availability

**BOOKING QUERIES** - Use `booking_management_tools` when users ask about:
- Keywords: "book", "booking", "reserve", "reservation", "cancel", "confirm", "customer", "my bookings"
- Examples: "Book this hotel", "Cancel my reservation", "Show my bookings", "Create a booking for John"
- Actions: Create, retrieve, or cancel bookings

**DECISION FRAMEWORK:**
1. **Primary Intent Recognition**: Identify the main service requested (hotel, flight, restaurant, car, booking)
2. **Secondary Services**: Check if the query involves multiple services for comprehensive planning
3. **Action Type**: Determine if it's a search, booking, or management action
4. **Parameter Extraction**: Extract relevant details like location, dates, preferences, customer names

**COMPLEX QUERY HANDLING:**
For queries involving multiple services (e.g., "Plan a trip to Paris with hotel and flights"):
1. Break down the query into component parts
2. Use multiple tools in logical sequence
3. Coordinate results to provide comprehensive travel plans
4. Ensure all aspects of the request are addressed

**RESPONSE GUIDELINES:**
- Always confirm what service you're helping with
- Ask for clarification if the query is ambiguous
- Provide complete information from tool results
- Offer additional relevant suggestions when appropriate
- Handle errors gracefully and suggest alternatives

**EXAMPLE ROUTING DECISIONS:**

Query: "Find luxury hotels in New York with pools"
→ Route to: `hotels_tools` (search by location + price tier + amenities)

Query: "Book a flight from Chicago to Miami on December 15th"
→ Route to: `flights_tools` (search by route + date) + `booking_management_tools` (create booking)

Query: "I need a complete trip to San Francisco - hotel, flight, and restaurant recommendations"
→ Route to: `hotels_tools` + `flights_tools` + `restaurants_tools` (coordinate all three)

Query: "Cancel booking ID 12345"
→ Route to: `booking_management_tools` (cancel booking)

Query: "What's on the menu at restaurant ID 5?"
→ Route to: `restaurants_tools` (get menu information)

**IMPORTANT NOTES:**
- Always use the most specific tool for the primary request
- When in doubt, ask the user for clarification rather than guessing
- Provide context about what information is needed for better results
- If a tool doesn't return expected results, try alternative approaches or explain limitations
- Remember that booking actions require specific details (customer name, dates, amounts)
- Consider follow-up questions that might help complete the user's travel planning

Use your natural language understanding to interpret user intent accurately and route queries to the appropriate tools for the best possible travel assistance experience."""
    ),
    tools=[booking_management_tool, car_rental_tool,
           flights_tool, hotels_tool, restaurants_tool],
)

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="travel_coordinator_agent",
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
