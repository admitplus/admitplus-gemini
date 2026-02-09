from typing import List, Dict


def build_generate_essay_question_prompt(
    university_name: str, degree: str, title: str, description: str
) -> List[Dict[str, str]]:
    """
    Build a prompt for generating personalized essay questions based on university, degree, essay title, and description.

    This function generates 3-5 personalized questions that help students think about how to write their essay
    for a specific university and degree program.

    Args:
        university_name: Name of the target university
        degree: Degree level (e.g., "Bachelor", "Master", "PhD")
        title: Essay title/prompt
        description: Essay description or requirements

    Returns:
        List of message dictionaries formatted for LLM chat API
    """
    system_prompt = (
        "You are an expert admissions counselor with deep knowledge of university-specific application requirements, "
        "program characteristics, and what makes compelling essays for different degree levels and fields of study. "
        "Your task is to generate 3-5 highly personalized, thought-provoking questions that will help a student "
        "brainstorm and develop their essay content for a SPECIFIC university, degree program, and essay prompt.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. Output ONLY valid JSON. No markdown, no code blocks, no explanatory text before or after the JSON.\n"
        "2. Generate exactly 3-5 questions (preferably 4-5 for better coverage).\n"
        "3. Each question MUST be uniquely tailored to the specific combination of university, degree level, and essay topic provided.\n"
        "4. Questions should be open-ended, thought-provoking, and encourage deep reflection.\n"
        "5. Ensure all JSON syntax is correct and parseable.\n\n"
        "PERSONALIZATION REQUIREMENTS:\n"
        "- Research and incorporate the university's unique values, mission, academic strengths, or distinctive features.\n"
        "- Consider the degree level context (Bachelor's focus on exploration/growth, Master's on specialization/career, PhD on research/passion).\n"
        "- Reflect the specific essay prompt's themes, requirements, and what the admissions committee is seeking.\n"
        "- Each question should be so specific that it would NOT make sense if applied to a different university or program.\n"
        "- Avoid generic questions that could apply to any application essay.\n\n"
        "QUESTION QUALITY GUIDELINES:\n"
        "- Questions should help students identify their unique stories, experiences, and perspectives relevant to THIS specific essay.\n"
        "- Each question should explore a different dimension: motivation/interest, fit/alignment, experiences/background, goals/aspirations, growth/transformation, contribution/value-add.\n"
        "- Questions should guide students to connect their personal narrative to the university's values and program's characteristics.\n"
        "- Questions should be written in a warm, encouraging, and intellectually engaging tone.\n"
        "- Questions should prompt reflection on specific aspects that matter for THIS university's admissions process.\n"
        "- Consider what makes this university/program unique and how students can demonstrate genuine fit.\n\n"
        "OUTPUT FORMAT:\n"
        "Return a JSON object with a 'questions' array. Each question object must have:\n"
        "- 'question_id': A unique identifier (string, e.g., 'q1', 'q2', etc.)\n"
        "- 'question': The actual question text (string)\n"
    )

    user_prompt = (
        "Generate 3-5 highly personalized essay questions based on the following information:\n\n"
        f"Target University: {university_name}\n"
        f"Degree Level: {degree}\n"
        f"Essay Title/Prompt: {title}\n"
        f"Essay Description/Requirements: {description}\n\n"
        f"CONTEXT FOR PERSONALIZATION:\n"
        f"- Consider what makes {university_name} distinctive: its mission, values, academic reputation, unique programs, campus culture, or what it's known for.\n"
        f"- For {degree} level applications, consider what admissions committees typically seek at this stage (e.g., exploration vs. specialization vs. research focus).\n"
        f"- Analyze the essay prompt carefully: what themes, values, or qualities is it asking students to demonstrate?\n"
        f"- Think about how students can show genuine fit and alignment with this specific university and program.\n\n"
        f"QUESTIONS SHOULD HELP STUDENTS:\n"
        f"- Reflect deeply on WHY this specific university and program align with their academic and career goals\n"
        f"- Identify unique experiences, challenges, achievements, or perspectives that directly relate to the essay topic and program focus\n"
        f"- Connect their background, interests, and aspirations to what makes {university_name} and this {degree} program distinctive\n"
        f"- Articulate what they can contribute to this specific academic community and how they will thrive there\n"
        f"- Explore meaningful stories of growth, learning, or transformation that demonstrate qualities relevant to this essay\n"
        f"- Consider how their unique perspective or background adds value to this particular program\n\n"
        f"IMPORTANT:\n"
        f"- Each question must be so specific that it would be inappropriate or irrelevant if asked about a different university or program.\n"
        f"- Questions should reference or imply specific aspects of {university_name}, the {degree} level context, or the essay requirements.\n"
        "- Avoid generic prompts like 'Why are you interested in this program?' unless you can make it highly specific.\n"
        "- Ensure questions cover different aspects (motivation, fit, experiences, goals, growth, contribution) while remaining deeply personalized.\n\n"
        "REQUIRED JSON STRUCTURE:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question_id": "q1",\n'
        '      "question": "Your personalized question here"\n'
        "    },\n"
        "    {\n"
        '      "question_id": "q2",\n'
        '      "question": "Another personalized question here"\n'
        "    },\n"
        "    ... (3-5 questions total)\n"
        "  ]\n"
        "}\n\n"
        "OUTPUT ONLY THE JSON OBJECT. NO OTHER TEXT."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
