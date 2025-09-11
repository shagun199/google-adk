# helpers/utils.py

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


async def get_or_create_session(session_service: InMemorySessionService, user_id: str, session_id: str) -> str:
    session = await session_service.get_session(app_name="coordinator", user_id=user_id, session_id=session_id)
    if not session:
        print(f"Creating session {session_id} for user {user_id}")
        await session_service.create_session(app_name="coordinator", user_id=user_id, session_id=session_id)
    return session_id


async def process_query(runner: Runner, user_id: str, session_id: str, query: str) -> str:
    content = types.Content(role="user", parts=[types.Part(text=query)])

    response_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        print(f'event {event}')
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
    return response_text
