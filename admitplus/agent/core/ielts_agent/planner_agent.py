from google.adk.agents.llm_agent import Agent

from admitplus.config import settings

description = """A specialist in academic strategy and essay outlining. 
Use this agent to analyze student background data and university prompts 
to create a high-level strategic essay structure and key themes.
"""

instruction = """You are an expert college admissions consultant. 
Your task is to review the student's profile and the specific essay prompt. 
Do not write the full essay. Instead, provide a detailed bulleted outline that includes: 
1. A unique 'hook' based on the student's experiences. 
2. Three core values or themes to highlight. 
3. A logical flow for each paragraph. Focus on differentiation and strategic alignment 
with the target university's values.
"""


planner_agent = Agent(
    model=settings.GEMINI_TEXT_MODEL_HEAVY,
    name="planner_agent",
    description="Strategic planner who creates structured essay outlines from student data.",
    instruction="Analyze the student's background and create a logical, high-impact outline.",
    tools=[],
)
