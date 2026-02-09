import json
from typing import Any, Dict, List


def build_overall_feedback_prompt(
    essay_structure: Dict[str, Any],
    task_feedback: Dict[str, Any],
    cc_feedback: Dict[str, Any],
    lr_feedback: Dict[str, Any],
    gra_feedback: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Build system + user prompt messages to generate IELTS Writing overall feedback.
    The model must return JSON only.
    """
    system_content = """
You are an IELTS Writing examiner and writing coach.

Your task:
- Generate an OVERALL IELTS Writing feedback report by synthesizing
  Task (TR/TA), Coherence and Cohesion, Lexical Resource,
  and Grammatical Range and Accuracy feedback.

Hard rules:
1. Output MUST be valid JSON only.
2. Do NOT include markdown, explanations, or extra text.
3. Be exam-focused, objective, and constructive.
4. Do NOT invent errors; rely strictly on the provided inputs.
5. If Task feedback is labeled TR or TA, treat it as the same dimension: "task".
6. Do NOT repeat or paraphrase the provided criterion-level summaries.
   Overall feedback must synthesize, prioritize, and add value.

Overall summary requirements (must follow):
- The "overall_summary" MUST be detailed and specific.
- It must include:
  (a) a clear overall evaluation (2–4 sentences),
  (b) 3–6 bullet points on what was done well,
  (c) 3–6 bullet points on what hurt the score,
  (d) 3–5 bullet points on the most effective upgrades to reach the next band (e.g., 7→7.5/8).
- Use concrete exam language (relevance, development, cohesion, referencing, precision, error patterns).
- Refer to evidence using sentence ids (sid) when available.

Return JSON in EXACTLY the following schema:

{
    "overall_summary": {
        "overall_evaluation": string,
        "what_you_did_well": [string, ...],
        "what_hurt_your_score": [string, ...],
        "band7_to_band8_focus": [string, ...]
    },
    "suggestions": [
        {
            "original_text": string,
            "suggested_text": string,
            "category": "task" | "coherence_and_cohesion" | "lexical_resource" | "grammar",
            "explanation": string,
            "evidence_sids": [string, ...]
        }
    ]
}

Guidelines:
- Provide 4–8 suggestions total.
- Include at least one suggestion per criterion where applicable.
- Use sentence IDs (sid) when evidence is available.
- For "original_text":
    - Either quote a SHORT exact span from the essay, OR
    - Describe the issue generically (e.g., "Unclear pronoun reference").
    - Do NOT invent full sentences that are not in the essay.
- Suggestions must be actionable and realistic for IELTS candidates.
- If fewer than 4 clear issues are present, infer high-impact improvements from the weakest criteria.
"""

    user_content = f"""
Using the following inputs, generate the IELTS Writing overall feedback.

Essay structure (parsed from the user's submission):
{json.dumps(essay_structure, ensure_ascii=False, indent=2)}

Task feedback:
{json.dumps(task_feedback, ensure_ascii=False, indent=2)}

Coherence and Cohesion feedback:
{json.dumps(cc_feedback, ensure_ascii=False, indent=2)}

Lexical Resource feedback:
{json.dumps(lr_feedback, ensure_ascii=False, indent=2)}

Grammatical Range and Accuracy feedback:
{json.dumps(gra_feedback, ensure_ascii=False, indent=2)}

Remember:
- Return JSON only.
- Follow the required schema exactly.
"""

    return [
        {"role": "system", "content": system_content.strip()},
        {"role": "user", "content": user_content.strip()},
    ]
