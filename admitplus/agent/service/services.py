import json
from typing import AsyncGenerator

from google.adk.runners import Runner

# from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.runners import RunConfig
from admitplus.agent.core.root_agent import root_agent
from admitplus.agent.service.redis_session_service import RedisSessionService
from admitplus.database.redis import redismanager


class AgentService:
    def __init__(self):
        # self.session_service = InMemorySessionService()
        self.session_service = RedisSessionService(redismanager.pool)

        self.agent = root_agent
        self.runner = Runner(
            agent=self.agent,
            app_name="root_agent",
            session_service=self.session_service,
        )

    async def stream_request(
        self, user_id: str, session_id: str, message: str
    ) -> AsyncGenerator[str, None]:
        _session = await self.session_service.get_session(
            app_name="root_agent", user_id=user_id, session_id=session_id
        )
        if not _session:
            await self.session_service.create_session(
                app_name="root_agent", user_id=user_id, session_id=session_id
            )

        content = types.Content(role="user", parts=[types.Part(text=message)])
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
            run_config=RunConfig(streaming_mode="sse"),
        ):
            text_chunk = ""
            if event.content and event.content.parts:
                text_chunk = event.content.parts[0].text or ""
                _func_call = event.content.parts[0].function_call
                if _func_call:
                    agent_name = _func_call.args.get("agent_name")
                else:
                    agent_name = None
            yield f"data: {json.dumps({'text': text_chunk, 'agent_name': agent_name, 'is_final': event.is_final_response()})}\n\n"
            if event.is_final_response():
                break
