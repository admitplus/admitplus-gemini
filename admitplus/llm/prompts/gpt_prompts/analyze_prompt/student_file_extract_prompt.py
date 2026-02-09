from typing import List, Dict


def build_student_file_extract_prompt(text_content: str) -> List[Dict[str, str]]:
    """
    Build a prompt for extracting student profile information and highlights from uploaded student files.

    This function is used to analyze student files (resumes, personal statements, etc.) and extract:
    1. Student profile information (basic info, education history, test scores) matching StudentProfile schema
    2. Highlights (achievements, research, work experience, awards, etc.) matching StudentHighlightCreateRequest schema

    Args:
        text_content: The extracted text content from the student file

    Returns:
        List of message dictionaries formatted for LLM chat API
    """
    system_prompt = (
        "You are an expert information extraction specialist specializing in academic and professional profile analysis. "
        "Your task is to extract structured student profile data and highlights from unstructured text documents "
        "(resumes, CVs, personal statements, transcripts, etc.) and output valid JSON that strictly conforms to the specified schema.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. Output ONLY valid JSON. No markdown, no code blocks, no explanatory text before or after the JSON.\n"
        "2. All field names and data types must exactly match the specified schema.\n"
        "3. Use null for missing optional fields. Use empty arrays [] for missing list fields.\n"
        "4. Ensure all JSON syntax is correct and parseable.\n\n"
        "EXTRACTION METHODOLOGY:\n"
        "1. Analyze the text to determine the student's current academic stage (high_school, undergraduate, graduate, phd, unknown).\n"
        "2. Extract education history records based on the identified stage:\n"
        "   - High school students: Extract high school education records (level: 'high_school')\n"
        "   - Undergraduate students: Extract undergraduate records (level: 'bachelor') and any prior high school records\n"
        "   - Graduate students: Extract graduate records (level: 'master' or 'phd') and prior undergraduate/high school records\n"
        "3. For each education record, infer the education level based on context (school type, degree mentioned, academic progression).\n"
        "4. Extract test scores and map them to standardized fields (IELTS, TOEFL, SAT, ACT, GRE, GMAT).\n"
        "5. Extract highlights with appropriate importance scores (0.0-1.0) based on significance and relevance.\n"
        "6. Generate relevant tags for each highlight based on content analysis.\n\n"
        "DATA QUALITY STANDARDS:\n"
        "- Extract exact values when explicitly stated in the text.\n"
        "- Make reasonable inferences only when context strongly supports them.\n"
        "- For dates, extract year as integer (YYYY format). Use null if not available.\n"
        "- For GPA, extract as float. Use null if not available.\n"
        "- For names, split into first_name and last_name based on common patterns.\n"
        "- For email and phone, extract exactly as written.\n"
        "- Mark current education records with is_current: true."
    )

    user_prompt = (
        "Extract student profile information and highlights from the following text. "
        "Output ONLY valid JSON matching the exact structure specified below.\n\n"
        "REQUIRED JSON STRUCTURE:\n"
        "{\n"
        '  "stage": "high_school" | "undergraduate" | "graduate" | "phd" | "unknown",\n'
        '  "basic_info": {\n'
        '    "first_name": "string (required)",\n'
        '    "last_name": "string (required)",\n'
        '    "gender": "string | null",\n'
        '    "dob": "YYYY-MM-DD | null",\n'
        '    "email": "string | null",\n'
        '    "phone": "string | null"\n'
        "  },\n"
        '  "education": {\n'
        '    "current_school": "string | null",\n'
        '    "grade": "string | null",\n'
        '    "curriculum": "string | null (e.g., AP, IB, A-Level, etc.)",\n'
        '    "gpa": "float | null"\n'
        "  },\n"
        '  "test_scores": {\n'
        '    "ielts": "string | null (e.g., "7.5" or "Overall: 7.5, Listening: 8.0")",\n'
        '    "toefl": "string | null (e.g., "110" or "110/120")",\n'
        '    "sat": "string | null (e.g., "1500" or "1500/1600")",\n'
        '    "act": "string | null (e.g., "32" or "32/36")",\n'
        '    "gre": "string | null (e.g., "320" or "Verbal: 160, Quant: 160")",\n'
        '    "gmat": "string | null (e.g., "700" or "700/800")"\n'
        "  },\n"
        '  "education_history": [\n'
        "    {\n"
        '      "level": "high_school" | "bachelor" | "master" | "phd" | "other",\n'
        '      "school_name": "string (required)",\n'
        '      "major": "string | null",\n'
        '      "curriculum": "string | null (for high school: AP, IB, A-Level, etc.)",\n'
        '      "start_year": "integer | null (YYYY format)",\n'
        '      "end_year": "integer | null (YYYY format, null if ongoing)",\n'
        '      "gpa": "float | null",\n'
        '      "is_current": "boolean (true if this is the current/most recent education)"\n'
        "    }\n"
        "  ],\n"
        '  "highlights": [\n'
        "    {\n"
        '      "category": "string (required, e.g., "research", "volunteer", "work_experience", "awards", "internship", "competitions", "activities", "other")",\n'
        '      "text": "string (required, detailed description of the achievement/experience)",\n'
        '      "importance_score": "float (required, 0.0 to 1.0, higher for more significant achievements)",\n'
        '      "tags": ["string"] (array of relevant keywords/tags),\n'
        '      "source_type": "file_analysis",\n'
        '      "source_id": "string | null"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "EDUCATION LEVEL DETERMINATION RULES:\n"
        "- Analyze the text to identify the student's current academic stage:\n"
        '  * If currently in high school or applying to undergraduate programs → stage: "high_school"\n'
        '  * If currently in undergraduate program or applying to graduate programs → stage: "undergraduate"\n'
        '  * If currently in master\'s program or applying to PhD → stage: "graduate"\n'
        '  * If currently in PhD program → stage: "phd"\n'
        '  * If unclear → stage: "unknown"\n'
        "- Education history records should be ordered chronologically (oldest first).\n"
        "- The most recent/current education should have is_current: true.\n"
        '- For high school students, education_history should contain high school records (level: "high_school").\n'
        "- For undergraduate students, education_history should contain:\n"
        '  * High school records (level: "high_school")\n'
        '  * Undergraduate records (level: "bachelor")\n'
        "- For graduate students, education_history should contain:\n"
        '  * High school records (level: "high_school")\n'
        '  * Undergraduate records (level: "bachelor")\n'
        '  * Graduate records (level: "master" or "phd")\n\n'
        "HIGHLIGHT EXTRACTION GUIDELINES:\n"
        "- Extract meaningful achievements, experiences, and accomplishments.\n"
        "- Assign importance_score based on:\n"
        "  * 0.8-1.0: Exceptional achievements (major awards, publications, significant leadership roles)\n"
        "  * 0.6-0.7: Notable achievements (research projects, internships, competitions)\n"
        "  * 0.4-0.5: Standard activities (volunteer work, clubs, regular work experience)\n"
        "  * 0.0-0.3: Minor activities or less relevant information\n"
        '- Generate 3-7 relevant tags per highlight based on content (e.g., ["machine learning", "Python", "research"]).\n'
        "- Use descriptive text that provides context and details about the achievement.\n"
        "- Categorize highlights appropriately:\n"
        '  * Research projects → category: "research"\n'
        '  * Volunteer activities → category: "volunteer"\n'
        '  * Work experience/internships → category: "work_experience" or "internship"\n'
        '  * Awards and honors → category: "awards"\n'
        '  * Competitions → category: "competitions"\n'
        '  * Clubs, sports, activities → category: "activities"\n'
        '  * Other notable achievements → category: "other"\n\n'
        "TEXT TO ANALYZE:\n"
        f"{text_content}\n\n"
        "OUTPUT ONLY THE JSON OBJECT. NO OTHER TEXT."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
