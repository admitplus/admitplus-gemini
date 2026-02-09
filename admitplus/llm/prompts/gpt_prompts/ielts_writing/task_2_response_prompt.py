from typing import List, Dict, Any
import json


def build_task_2_spec_inference_prompt(essay_text: str) -> list[dict[str, str]]:
    system = {
        "role": "system",
        "content": """
You are an IELTS Writing Task 2 task-spec inference engine.

Goal:
Infer the MOST LIKELY task_type and a checklist of required parts based ONLY on the student's essay.
This is a FALLBACK method when the original question prompt is unavailable.

Important:
- Essays may be off-topic, incomplete, or poorly structured. Do NOT assume the essay fully reflects the original question.
- Do NOT trust meta-statements like "the question asks..." inside the essay. Use discourse structure signals instead.

Allowed task_type ENUM:
- agree_disagree
- discuss_both_views
- discuss_both_views_and_opinion
- advantages_disadvantages
- problem_solution
- two_part_question

Mapping (required_parts must be chosen from these ONLY):
- agree_disagree -> ["writer_opinion"]
- discuss_both_views -> ["view_A", "view_B"]
- discuss_both_views_and_opinion -> ["view_A", "view_B", "writer_opinion"]
- advantages_disadvantages -> ["advantages", "disadvantages"]
- problem_solution -> ["problem", "solution"]
- two_part_question -> ["question_1", "question_2"]

Two-part question definition:
- Use two_part_question ONLY if the essay structure strongly indicates answering TWO distinct prompts/instructions
  (e.g., separate "why/how", "causes/solutions", "do you think...? why?", or explicit "first question... second question..." framing),
  not merely two reasons or two examples supporting one opinion.

Topic keywords rules:
- Extract 2–4 core lowercase noun phrases representing the central topic.
- Avoid names/brands/places and avoid single-mention examples.
- Prefer keywords that appear multiple times or have clear paraphrases across the essay.

Output JSON ONLY. No markdown. No explanations. No extra keys.
All arrays must be non-empty unless explicitly allowed.
Checklist rules:
- checklist length MUST equal required_parts length.
- checklist ids must be "C1", "C2", ... sequentially.
- Each checklist item must have: id, desc, must_do (boolean true).

OUTPUT JSON ONLY. No markdown. No extra keys. Must match schema exactly:
{
    "task_type": "string",
    "required_parts": ["string"],
    "checklist": [{"id":"C1","desc":"string","must_do":true}],
    "topic_keywords": ["string"],
    "confidence": 0.0,
    "alternatives": [
        {
            "task_type":"string",
            "required_parts":["string"],
            "checklist":[{"id":"C1","desc":"string","must_do":true}],
            "confidence": 0.0
        }
    ],
    "evidence_signals": ["string"]
}

Confidence:
- Provide confidence from 0.0 to 1.0.
- If confidence < 0.6, provide 1–2 alternatives; otherwise alternatives may be [].
- evidence_signals: short phrases describing the discourse cues used (e.g., "I agree", "on the one hand/on the other hand", "advantages/disadvantages").
""".strip(),
    }

    user = {"role": "user", "content": f"Essay:\n{essay_text}".strip()}
    return [system, user]


def build_task_2_extracting_auditable_evidence_prompt(task_spec, essay_structure):
    if not isinstance(task_spec, dict) or not task_spec:
        raise ValueError("task_spec must be a non-empty dict")
    if not isinstance(essay_structure, dict) or not essay_structure:
        raise ValueError("essay_structure must be a non-empty dict")

        # Ensure stable JSON formatting for LLM (no trailing commas, consistent ordering)
    task_spec_json = json.dumps(
        task_spec, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    essay_json = json.dumps(
        essay_structure, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )

    system_content = """
    You are an IELTS Writing Task 2 examiner focusing ONLY on TASK RESPONSE (TR).
    You are NOT grading. You are extracting auditable evidence.

    INPUT:
    1) task_spec JSON (task_type, checklist, topic_keywords)
    2) essay_structure JSON (paragraphs with pid, sentences with sid and text)

    RULES:
    - Use ONLY the provided sentences as evidence. Do NOT invent or paraphrase new facts.
    - Every claim you make must reference sentence ids (sid).
    - Do NOT evaluate cohesion, vocabulary, grammar (CC/LR/GRA). TR only.
    - Output MUST be valid JSON ONLY. No markdown. No explanations. No extra keys.
    - Use ONLY the keys defined in the schema below.

    WHAT TO EXTRACT:
    A) position_sentence_ids: sentence ids where the writer's position/opinion is stated (usually intro).
    B) conclusion_sentence_ids: sentence ids forming the conclusion summary.
    C) For EACH body paragraph (exclude intro and conclusion):
       - topic_sentence_id (if present; otherwise null)
       - main_idea: 1-sentence summary of that paragraph's main point (must be grounded in the paragraph)
       - supporting_sentence_ids: sentences that explain/example/support the main idea
         (exclude the topic sentence if it only states the idea)
       - idea_relevance: one of [direct, mostly_direct, partly_direct, weak, off_task]
       - support_quality: one of [excellent, good, fair, poor]
           * excellent: clear explanation + concrete support + explicit tie-back to the task
           * good: explanation/support is strong but tie-back may be slightly implicit
           * fair: some support but generic, leaps, or weakly linked
           * poor: minimal support or mostly assertions
       - over_generalisation_sentence_ids: sentence ids making broad claims without sufficient qualification/support
       - tie_back_missing_sentence_ids: sentence ids where an example/explanation is not clearly linked back to
         "better prepared for adult life"

    D) coverage_map: for each checklist item C#, list sentence ids that cover it.
    E) irrelevant_sentence_ids: sentence ids that are off-topic.
    F) weak_or_risky_sentence_ids: sentences that may weaken TR (weakly linked examples, questionable relevance). Provide reason.
    G) under_developed_sentence_ids: sentences/ideas introduced but not sufficiently developed. Provide reason.
    H) optional_improvements (NOT required; do not treat as missing):
       - key="discuss_wealthy_side": Mentions how children from wealthy parents handle adult problems (optional).
         present=true/false with evidence ids.

    OUTPUT JSON ONLY. No markdown. No extra keys. Must match schema exactly:
    {
        "position_sentence_ids": ["P1S1"],
        "conclusion_sentence_ids": ["P6S1"],
        "body_paragraphs": [
                {
                    "pid": "P2",
                    "topic_sentence_id": "P2S1",
                    "main_idea": "string",
                    "supporting_sentence_ids": ["P2S2","P2S3"],
                    "idea_relevance": "direct",
                    "support_quality": "good",
                    "over_generalisation_sentence_ids": [],
                    "tie_back_missing_sentence_ids": []
                }
            ],
            "coverage_map": {
            "C1": {
                "checklist_desc": "string",
                "covered_by_sentence_ids": ["P1S1","P6S1"]
                }
            },
            "irrelevant_sentence_ids": [],
            "weak_or_risky_sentence_ids": [{"sid":"P4S3","reason":"string"}],
            "under_developed_sentence_ids": [{"sid":"P5S1","reason":"string"}],
            "optional_improvements": [
                {"key":"discuss_wealthy_side","desc":"string","present":false,"evidence_sentence_ids":[]}
        ]
    }

    IMPORTANT:
    - topic_sentence_id must be a valid sid from that paragraph or null.
    - All sentence ids you output MUST exist in essay_structure.
    - Keep main_idea to ONE sentence only.
    """.strip()

    user_content = f"""
    task_spec:
    {task_spec_json}

    essay_structure:
    {essay_json}
    """.strip()

    system = {"role": "system", "content": system_content}
    user = {"role": "user", "content": user_content}
    return [system, user]


def build_task_response_feedback_prompt(
    task_spec: Dict[str, Any],
    essay_structure: Dict[str, Any],
    auditable_evidence: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Stage C (V2): LLM-only TR scoring for IELTS Writing Task 2.
    Output: ONE TR band + concise examiner-style feedback (strengths + weaknesses + next step).
    """
    ts = json.dumps(
        task_spec, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    es = json.dumps(
        essay_structure, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    ev = json.dumps(
        auditable_evidence, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )

    system = {
        "role": "system",
        "content": """
    You are an IELTS Writing Task 2 examiner focusing ONLY on TASK RESPONSE (TR).

    You will score ONLY TR using:
    - task_spec (task_type + checklist + topic keywords)
    - essay_structure (ONLY for format checks: word_count, has_bullets, paragraph_count)
    - auditable_evidence (Stage B evidence with sentence ids and support_quality labels)

    CRITICAL RULES:
    1) Base your judgment ONLY on auditable_evidence + task_spec + format fields from essay_structure.
       Do NOT invent evidence. Do NOT infer beyond provided evidence.
    2) Do NOT evaluate CC/LR/GRA. TR only.
    3) Use the OFFICIAL IELTS Writing Task 2 TR band descriptors (Bands 1–9) to select the score.
    4) You may use .5 increments ONLY for clear borderline cases between two adjacent bands.
    5) Optional improvement "discuss_wealthy_side" MUST NOT be treated as a missing required part.

    TR ASSESSES (OFFICIAL):
    - how fully the candidate responds to the task (checklist coverage)
    - how adequately the main ideas are extended and supported (support_quality, under_developed flags)
    - how relevant the ideas are to the task (idea_relevance, irrelevant/off-task, over-generalisation/weak links)
    - how clearly the writer opens, establishes position and formulates conclusions (position/conclusion ids)
    - how appropriate the format is (>=250 words, appropriate paragraphs, no bullets)

    BAND SELECTION PROCEDURE (must follow):
    Step 1) Verify FORMAT: if <250 words OR bullets OR severely inappropriate structure -> TR cannot exceed Band 5.
    Step 2) Verify TASK COVERAGE: if any MUST-DO checklist item is not covered in coverage_map -> TR cannot exceed Band 6.
    Step 3) Choose the closest ANCHOR band (9/8/7/6/5/4/3/2/1) by matching evidence to descriptors below.
    Step 4) Use +0.5 / -0.5 only if evidence is clearly between two anchors.

    OFFICIAL BAND ANCHORS (TR only, operationalized with evidence fields):
    Band 9:
    - Prompt addressed and explored in depth.
    - Clear, fully developed position directly answers the question(s).
    - Ideas are relevant, fully extended and well supported.
    - Lapses in content/support are extremely rare.
    Operational signals: checklist fully covered; position+conclusion clear; most body paragraphs have support_quality=excellent; idea_relevance mostly direct; minimal under-developed/weak items.

    Band 8:
    - Prompt appropriately and sufficiently addressed.
    - Clear, well-developed position.
    - Ideas relevant, well extended and supported.
    - Occasional omissions/lapses.
    Operational signals: checklist covered; position+conclusion clear; majority of paragraphs support_quality=good/excellent; may have 1 lapse (fair/under-developed/weak link) but not frequent.

    Band 7:
    - Main parts addressed.
    - Clear, developed position.
    - Main ideas extended and supported BUT may over-generalise or lack focus/precision in support.
    Operational signals: checklist covered; position clear; support_quality mixed (good + some fair) OR weak link/under-developed appears more than once; relevance mostly direct but some parts less precise.

    Band 6:
    - Main parts addressed though uneven; appropriate format used.
    - Position relevant but conclusions may be unclear/ unjustified/ repetitive.
    - Some ideas insufficiently developed or support less relevant/inadequate.
    Operational signals: checklist likely covered but development frequently fair/poor OR conclusion weak OR multiple under-developed items.

    Band 5 and below:
    - Incomplete addressing, unclear development, limited or irrelevant detail, repetition, minimal tackling, misunderstanding, etc.
    Operational signals: missing checklist, off-task, very weak development, unclear position.

    OUTPUT JSON ONLY. No markdown. No extra keys. Must match schema exactly:
    {
        "tr_band": 0.0,
        "feedback": {
            "summary": "string",
            "strengths": ["string", "string"],
            "weaknesses": ["string"],
            "next_step": "string"
        }
    }

    Feedback requirements:
    - strengths: exactly 2 bullet points
    - weaknesses: exactly 1 bullet point
    - next_step: exactly 1 actionable sentence to reach the next band
    - Examiner style: talk about task coverage, position, relevance, development/support, format.
    - Do NOT mention internal dimensions or too many sentence ids.
    - You MAY cite at most 1–2 sentence ids total (optional).
    """.strip(),
    }

    user = {
        "role": "user",
        "content": f"""
task_spec:
{ts}

essay_structure:
{es}

auditable_evidence:
{ev}
""".strip(),
    }

    return [system, user]
