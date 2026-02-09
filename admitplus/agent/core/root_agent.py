from google.adk.agents.llm_agent import Agent

from admitplus.agent.core.admission_agent.admissions_root import admissions_agent
from admitplus.agent.core.ielts_agent.writing_root_agent import ielts_writing_root_agent
from admitplus.config import settings


description = """
Top-level router for AdmitPlus. Routes the user to admissions (personal statements, applications) or to IELTS writing (tasks, scoring, feedback) based on intent.
"""

instruction = """
You are the root agent. Your job is to understand what the user wants and delegate to the right sub-agent.

- For admissions-related requests (personal statements, application essays, school lists, etc.), delegate to admissions_agent.
- For IELTS writing (practice tasks, submitting essays, getting scores and feedback), delegate to ielts_writing_root_agent.

Do not do the work yourself. Always hand off to the appropriate sub-agent and return their response to the user in a clear way.
"""


root_agent = Agent(
    model=settings.GEMINI_TEXT_MODEL_DEFAULT,
    name="root_agent",
    description=description,
    instruction=instruction,
    sub_agents=[admissions_agent, ielts_writing_root_agent],
)
