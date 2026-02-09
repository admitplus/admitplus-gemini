def build_generate_essay_prompt(essay_record: dict, question: list) -> list:
    """
    Build a prompt for generating an admissions essay based on university, program, essay requirements, and student's Q&A responses.

    Args:
        essay_record: Dictionary containing essay metadata:
            - target_university: Name of the target university
            - target_degree_level: Degree level (e.g., "Bachelor", "Master", "PhD")
            - target_major: Program/major name
            - essay_type: Type of essay (e.g., "personal_statement", "statement_of_purpose")
            - essay_description: Essay prompt/description/requirements
        question: List of question dictionaries, each containing:
            - question: The question text
            - answer: The student's answer to the question

    Returns:
        List of message dictionaries formatted for LLM chat API
    """

    # Format questions and answers
    qa_pairs = []
    for idx, qa in enumerate(question, 1):
        q_text = qa.get("question", "")
        a_text = qa.get("answer", "")
        if q_text and a_text:
            qa_pairs.append(f"Q{idx}: {q_text}\nA{idx}: {a_text}")

    qa_content = (
        "\n\n".join(qa_pairs) if qa_pairs else "No questions and answers provided."
    )

    # Get essay description/prompt
    essay_description = essay_record.get(
        "essay_description", essay_record.get("prompt_text", "")
    )

    system_prompt = f"""
You are an expert admissions essay writer specializing in crafting compelling, personalized application essays for elite universities.

Your task is to generate a complete and compelling {essay_record.get("essay_type", "essay").replace("_", " ")} for a student applying to a {essay_record.get("target_degree_level", "")} program in {essay_record.get("target_major", "")} at {essay_record.get("target_university", "")}.

CRITICAL REQUIREMENTS:

1. PERSONALIZATION & SPECIFICITY:
   - The essay MUST be highly personalized to {essay_record.get("target_university", "the target university")} and the {essay_record.get("target_degree_level", "")} program in {essay_record.get("target_major", "")}.
   - Demonstrate genuine fit and alignment with this specific university's values, program strengths, and what makes it distinctive.
   - Show deep understanding of why this particular program at this particular university aligns with the student's goals.
   - Avoid generic statements that could apply to any university or program.

2. CONTENT & STRUCTURE:
   - Base the essay entirely on the student's responses to the personalized questions provided below.
   - Weave together the student's answers into a coherent, compelling narrative that directly addresses the essay prompt.
   - Highlight the student's unique motivations, experiences, strengths, and authentic voice.
   - Have a clear narrative structure with emotional depth and vivid, specific details.
   - Reflect critical qualities like intellectual curiosity, creativity, perseverance, leadership, commitment, or other relevant attributes.

3. ESSAY TYPE & REQUIREMENTS:
   - Follow the requirements and expectations for a {essay_record.get("essay_type", "essay").replace("_", " ")}.
   - Address all aspects of the essay prompt/description provided.
   - Ensure the essay type-appropriate tone and focus (e.g., personal statement vs. statement of purpose).

4. WRITING QUALITY:
   - Write in fluent, polished English with a consistent and natural tone.
   - Use vivid, specific examples and concrete details rather than vague generalizations.
   - Show, don't tell - use storytelling to demonstrate qualities and experiences.
   - Maintain authenticity and avoid clichés or overly formal language.

5. OUTPUT FORMAT:
   - Return the full essay as plain text only.
   - No titles, no markdown formatting, no commentary, no explanations.
   - Just the essay body text.
"""

    user_prompt = f"""
Generate a personalized admissions essay based on the following information:

TARGET UNIVERSITY: {essay_record.get("target_university", "")}
DEGREE LEVEL: {essay_record.get("target_degree_level", "")}
PROGRAM/MAJOR: {essay_record.get("target_major", "")}
ESSAY TYPE: {essay_record.get("essay_type", "").replace("_", " ")}

ESSAY PROMPT/DESCRIPTION:
{essay_description}

STUDENT'S RESPONSES TO PERSONALIZED QUESTIONS:
{qa_content}

INSTRUCTIONS:
- Synthesize the student's responses into a cohesive, compelling narrative that directly addresses the essay prompt.
- Ensure the essay demonstrates why this student is an excellent fit for {essay_record.get("target_university", "this university")}'s {essay_record.get("target_degree_level", "")} program in {essay_record.get("target_major", "")}.
- Connect the student's experiences, motivations, and goals to what makes this university and program distinctive.
- Create a narrative that flows naturally and tells a compelling story about the student's journey and aspirations.
- Use specific details from the student's answers to make the essay authentic and memorable.
- Ensure the essay type ({essay_record.get("essay_type", "").replace("_", " ")}) is appropriate for the content and structure.

Generate the complete essay now.
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


# def build_ai_essay_prompt(input_data: dict) -> list:
#     essay_req = input_data.get("essay_requirement", {})
#     writing = input_data.get("writing_settings", {})
#
#     system_prompt = f"""
# You are an expert admissions essay writer for elite U.S. universities.
# Your goal is to generate a {essay_req.get('essay_type', 'personal statement').replace('_', ' ')} that helps the student stand out in {input_data.get('target_university')}'s {input_data.get('target_degree_level')} application for {input_data.get('target_major')}.
#
# Requirements:
# - Use the specified structure template: {writing.get('structure_template', 'STAR')} (e.g., STAR, 5-paragraph, or Problem-Growth-Reflection).
# - Maintain a {writing.get('tone', 'Reflective')} tone, in {writing.get('narrative_perspective', 'First Person')} perspective.
# - Follow natural {writing.get('language_preference', 'American English')} conventions.
# - Focus on clarity, authenticity, and emotional depth.
# - Integrate academic, extracurricular, and award materials meaningfully to show personal growth, motivation, and impact.
# - Keep within approximately {essay_req.get('word_limit', '650')} words.
# - Output only the final essay body text, with no titles, commentary, or markdown formatting.
# - Only use information explicitly provided in the materials and memory. Do not invent new facts or experiences.
#
# You are encouraged to balance storytelling and reflection, showing how past experiences connect to future goals.
# """.strip()
#
#     materials_formatted = "\n".join([
#         f"- [{m['category']}] {m['title']}: {m['description']}"
#         for m in input_data.get("materials", [])
#     ])
#     memory_formatted = "\n".join([f"- {mem}" for mem in input_data.get("memory", [])])
#
#     user_prompt = f"""
# Essay topic: {input_data.get('essay_topic')}
#
# Essay prompt requirement:
# {essay_req.get('prompt_text')}
#
# Student's materials:
# {materials_formatted}
#
# Conversation memory / personal background:
# {memory_formatted}
#
# Writing settings:
# Tone: {writing.get('tone')}
# Narrative Perspective: {writing.get('narrative_perspective')}
# Language Preference: {writing.get('language_preference')}
# Structure Template: {writing.get('structure_template')}
# Generation Goal: {writing.get('generation_goal')}
# Length Control: {writing.get('length_control')}
#
# Please generate a personalized, coherent, and emotionally engaging essay draft.
# """.strip()
#
#     return [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": user_prompt}
#     ]
