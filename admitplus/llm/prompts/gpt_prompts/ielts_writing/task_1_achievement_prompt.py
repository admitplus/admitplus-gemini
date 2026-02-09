from typing import List, Dict, Any
import json


def build_task_1_spec_inference_prompt(
    essay_text: str, image_text: str
) -> list[dict[str, str]]:
    system = {
        "role": "system",
        "content": """
You are an IELTS Writing Task 1 Academic task-spec inference engine.

Goal:
Infer the MOST LIKELY Task 1 input type and produce a checklist of required parts,
based on:
(1) the student's Task 1 response (essay_text), AND
(2) extracted visual description text from the chart/graph/map/process (image_text).

Important:
- This is used when the original prompt is unavailable.
- Do NOT guess beyond the given image_text and essay_text.
- Do NOT accept speculative explanations outside the given data.

Allowed task_type ENUM (choose ONE):
- line_graph
- bar_chart
- pie_chart
- table
- process_diagram
- map
- mixed
- unknown

Required parts must be chosen ONLY from this set:
- overview
- key_features
- comparisons
- accurate_reporting
- stages
- sequence
- locations
- changes

Mapping rules (examples):
- line_graph/bar_chart/pie_chart/table/mixed:
  required_parts MUST include: ["overview","key_features","comparisons","accurate_reporting"]
- process_diagram:
  required_parts MUST include: ["overview","stages","sequence"]
- map:
  required_parts MUST include: ["overview","locations","changes","comparisons"]
- unknown:
  required_parts MUST include at least ["overview","key_features"]

Checklist rules:
- checklist length MUST equal required_parts length.
- checklist ids must be "C1", "C2", ... sequentially.
- Each checklist item must have: id, desc, must_do (boolean true).

Topic keywords rules:
- Extract 2–4 core lowercase noun phrases describing the subject shown in the visual (not the essay opinions).
- Avoid names/brands/places unless the map requires them (then keep major location names).
- Prefer nouns that appear in image_text.

Output JSON ONLY. No markdown. No explanations. No extra keys. Must match schema exactly:
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
- evidence_signals: short phrases describing cues used from image_text and essay_text
  (e.g., "percentages", "from 2000 to 2020", "process stages", "two maps show changes").
""".strip(),
    }

    user = {
        "role": "user",
        "content": f"""
image_text:
{(image_text or "").strip()}

essay_text:
{(essay_text or "").strip()}
""".strip(),
    }
    return [system, user]


def build_task_1_extracting_auditable_evidence_prompt(
    task_spec: Dict[str, Any],
    essay_structure: Dict[str, Any],
    image_text: str,
) -> List[Dict[str, str]]:
    if not isinstance(task_spec, dict) or not task_spec:
        raise ValueError("task_spec must be a non-empty dict")
    if not isinstance(essay_structure, dict) or not essay_structure:
        raise ValueError("essay_structure must be a non-empty dict")

    task_spec_json = json.dumps(
        task_spec, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    essay_json = json.dumps(
        essay_structure, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    image_text_safe = (image_text or "").strip()

    system_content = """
You are an IELTS Writing Task 1 Academic examiner focusing ONLY on TASK ACHIEVEMENT (TA).
You are NOT grading. You are extracting auditable evidence.

INPUT:
1) task_spec JSON (task_type, checklist, topic_keywords)
2) image_text (facts extracted from the visual input)
3) essay_structure JSON (paragraphs with pid, sentences with sid and text)

RULES:
- Use ONLY the provided sentences as evidence. Do NOT invent or paraphrase new facts.
- Every claim you make must reference sentence ids (sid).
- Do NOT evaluate cohesion, vocabulary, grammar (CC/LR/GRA). TA only.
- Do NOT introduce speculative explanations beyond the data in image_text.
- Output MUST be valid JSON ONLY. No markdown. No explanations. No extra keys.
- Use ONLY the keys defined in the schema below.

WHAT TO EXTRACT (TA evidence):
A) intro_sentence_ids: sentence ids that introduce what the visual shows (paraphrase of task).
B) overview_sentence_ids: sentence ids that provide an OVERVIEW (main trends/stages/changes).
C) For EACH body paragraph (exclude intro and conclusion if any):
   - topic_sentence_id (if present; otherwise null)
   - main_feature: 1-sentence description of the key feature/trend/comparison covered in that paragraph
   - supporting_sentence_ids: sentences giving details (numbers, extremes, comparisons, stage descriptions)
   - data_or_feature_type: one of [trend, comparison, extreme, stage, location_change, category_breakdown, other]
   - accuracy_flag: one of [accurate, unclear, likely_inaccurate, unsupported]
   - accuracy_notes: short note why (must be grounded in image_text; if cannot verify, use 'unclear')

D) coverage_map: for each checklist item C#, list sentence ids that cover it.
E) missing_or_weak_areas: list of checklist ids that appear weakly evidenced (not missing required parts; just weak)
F) speculative_or_irrelevant_sentence_ids: sentences that go beyond data (e.g., reasons/causes/opinions) or are irrelevant.
G) inaccurate_or_unsupported_claims: [{"sid":"...","reason":"..."}] where claims contradict or exceed image_text.

OUTPUT JSON ONLY. Must match schema exactly:
{
    "intro_sentence_ids": ["P1S1"],
    "overview_sentence_ids": ["P2S1"],
    "body_paragraphs": [
        {
            "pid": "P2",
            "topic_sentence_id": "P2S1",
            "main_feature": "string",
            "supporting_sentence_ids": ["P2S2","P2S3"],
            "data_or_feature_type": "trend",
            "accuracy_flag": "accurate",
            "accuracy_notes": "string"
        }
    ],
    "coverage_map": {
        "C1": {
            "checklist_desc": "string",
            "covered_by_sentence_ids": ["P1S1","P2S1"]
        }
    },
    "missing_or_weak_areas": ["C2"],
    "speculative_or_irrelevant_sentence_ids": ["P3S2"],
    "inaccurate_or_unsupported_claims": [{"sid":"P4S1","reason":"string"}]
}

IMPORTANT:
- topic_sentence_id must be a valid sid from that paragraph or null.
- All sentence ids you output MUST exist in essay_structure.
- Keep main_feature to ONE sentence only.
- Use image_text to judge whether claims are supported; if you cannot verify, mark 'unclear' not 'inaccurate'.
""".strip()

    user_content = f"""
task_spec:
{task_spec_json}

image_text:
{image_text_safe}

essay_structure:
{essay_json}
""".strip()

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_task_1_task_achievement_feedback_prompt(
    task_spec: Dict[str, Any],
    essay_structure: Dict[str, Any],
    auditable_evidence: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    Stage C: LLM-only TA scoring for IELTS Writing Task 1 Academic.
    Output: ONE TA band + concise examiner-style feedback (2 strengths, 1 weakness, 1 next step).
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

    system_content = """
You are an IELTS Writing Task 1 ACADEMIC examiner focusing ONLY on TASK ACHIEVEMENT (TA).

You will produce:
- One TA band score (1.0–9.0, with .5 only if clearly borderline)
- Concise examiner-style feedback (2 strengths, 1 weakness, 1 next step)

You MUST base your judgment ONLY on:
- task_spec (task_type + checklist + topic keywords)
- essay_structure format fields (word_count, has_bullets, paragraph_count)
- auditable_evidence (coverage_map, overview_sentence_ids, body_paragraphs, accuracy flags, speculative/inaccurate lists)

CRITICAL RULES:
1) Do NOT invent evidence or rewrite the essay. Use only provided evidence fields.
2) Do NOT evaluate CC/LR/GRA. TA only.
3) Do NOT speculate about the chart beyond what is in auditable_evidence.
4) If you cite evidence, cite at most 1–2 sentence ids (sid) total (optional).

TA (Task 1 Academic) assesses:
- how fully, appropriately, accurately and relevantly the response fulfils the task requirements (>=150 words)
- selecting key features and providing sufficient detail
- reporting figures/trends accurately
- making comparisons / highlighting main trends or differences (not purely mechanical listing)
- appropriate format

HARD CAPS / GATES (must follow):
A) If essay_structure.word_count <= 20 -> TA MUST be 1.0
B) If essay_structure.word_count < 150 OR essay_structure.has_bullets == true -> TA CANNOT exceed 5.0
C) If auditable_evidence.overview_sentence_ids is empty -> TA CANNOT exceed 6.0 (Band 7 requires a clear overview)
D) If auditable_evidence shows MULTIPLE inaccurate_or_unsupported_claims in key areas -> reduce the anchor band by at least 1

BAND ANCHORS (based on official TA descriptors, operationalized):
Band 9:
- All requirements fully and appropriately satisfied; extremely rare lapses.
Signals: checklist fully covered; clear overview; key features well selected and well supported; almost no inaccuracies/speculation.

Band 8:
- All requirements covered appropriately/relevantly/sufficiently; key features skilfully selected and clearly highlighted.
Signals: clear overview; strong selection; mostly accurate; occasional omissions/lapses.

Band 7:
- Requirements covered; content relevant and accurate with a few omissions/lapses; format appropriate.
- Clear overview; data appropriately categorised; main trends/differences identified.
Signals: overview present and clear; key features highlighted but could be extended/illustrated more; minor lapses.

Band 6:
- Focuses on requirements with appropriate format.
- Key features adequately highlighted; relevant overview attempted.
- Some irrelevant/inaccurate info may occur in detail; some missing/excess detail; more extension needed.
Signals: overview present but weak/attempted; development uneven; some unclear/unsupported details.

Band 5:
- Generally addresses requirements; format may be inappropriate in places.
- Key features not adequately covered; description mainly mechanical; may lack data support.
- Irrelevant/inaccurate material in key areas detracts; limited extension.
Signals: weak/no overview; mechanical listing; frequent unsupported claims or irrelevant detail.

Band 4–2:
- 4: attempt; few key features; format may be inappropriate; key features may be irrelevant/repetitive/inaccurate.
- 3: does not address requirements (possibly misunderstanding); key features largely irrelevant; limited/repetitive info.
- 2: barely relates to the task.

BORDERLINE (.5) RULE:
- Use .5 only if the evidence is clearly between two adjacent anchors AFTER applying caps.
- Never output a score that violates caps A/B/C.

OUTPUT JSON ONLY. No markdown. No extra keys. Must match schema exactly:
{
    "ta_band": 0.0,
    "feedback": {
        "summary": "string",
        "strengths": ["string", "string"],
        "weaknesses": ["string"],
        "next_step": "string"
    }
}

Feedback writing requirements:
- summary: 2–3 sentences max; mention overview + key features + accuracy/comparisons.
- strengths: exactly 2 bullets; focus on what supports the band.
- weaknesses: exactly 1 bullet; the main limiting factor.
- next_step: exactly 1 actionable sentence to reach the next band.
- Do NOT restate the full descriptors. Be specific and actionable.
""".strip()

    user_content = f"""
task_spec:
{ts}

essay_structure:
{es}

auditable_evidence:
{ev}
""".strip()

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
