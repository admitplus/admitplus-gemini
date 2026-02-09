import json
from typing import Any, Dict, List


def build_extracting_auditable_lr_evidence_prompt(
    essay_structure: Dict[str, Any],
) -> List[Dict[str, str]]:
    es = json.dumps(
        essay_structure, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )

    system = {
        "role": "system",
        "content": """
You are an IELTS Writing examiner focusing ONLY on LEXICAL RESOURCE (LR).
You are NOT grading. You are extracting auditable LR evidence.

INPUT:
- essay_structure JSON with paragraphs (pid) and sentences (sid, text)

RULES:
- Use ONLY the provided text as evidence. Do NOT invent or rewrite sentences.
- Do NOT evaluate TR/CC/GRA. LR only.
- Every item MUST reference sentence ids (sid).
- For errors/highlights you MUST include the exact span (substring) from the sentence.
- Output MUST be valid JSON ONLY. No markdown. No extra keys.

LR ASSESSES (OFFICIAL):
- range of general words used (synonyms/variation to avoid repetition)
- adequacy & appropriacy (topic-specific items, attitude markers)
- precision of word choice/expression
- control of collocations/idiomatic expressions/sophisticated phrasing
- density & communicative effect of spelling errors
- density & communicative effect of word formation errors

WHAT TO EXTRACT:
A) repetition:
- Identify repeated words/phrases that reduce lexical range.
- Return 3–8 items max. Each item: lemma_or_phrase, count (rough), example_sids (2–4).

B) vocabulary_highlights:
- Extract 4–10 strong lexical items/phrases showing good range/precision/topic appropriacy/collocation/sophisticated phrasing.
- Each highlight: sid, span, category in [topic_specific, attitude_marker, precise_wording, collocation, sophisticated_phrase], note.

C) lexical_errors:
- Extract lexical problems:
  error_type in [wrong_word_choice, collocation_error, register_inappropriate, awkward_phrase, spelling, word_formation]
- severity in [minor, moderate, major]
- impact in [minimal, some, impedes] (communication impact)
- Each error must include sid + exact span + short note.

D) summaries (descriptive, NOT a band score):
- range_level: [wide, sufficient, limited, extremely_limited]
- precision_level: [high, medium, low]
- collocation_control: [strong, adequate, weak]
- error_density: [low, medium, high]
- error_impact_overall: [minimal, some, impedes]

OUTPUT JSON ONLY. Must match schema exactly:
{
    "repetition": [
        {"
            lemma_or_phrase":"string",
            "count":0,
            "example_sids":["P2S1","P3S2"]
        }
    ],
    "vocabulary_highlights": [
        {
            "sid":"P2S1",
            "span":"string",
            "category":"topic_specific",
            "note":"string"
        }
    ],
    "lexical_errors": [
        {
            "sid":"P4S1",
            "span":"string",
            "error_type":"wrong_word_choice",
            "severity":"minor",
            "impact":"minimal",
            "note":"string"
        }
    ],
    "summaries": {
        "range_level":"wide|sufficient|limited|extremely_limited",
        "precision_level":"high|medium|low",
        "collocation_control":"strong|adequate|weak",
        "error_density":"low|medium|high",
        "error_impact_overall":"minimal|some|impedes"
    }
}
""".strip(),
    }

    user = {
        "role": "user",
        "content": f"""
essay_structure:
{es}
""".strip(),
    }

    return [system, user]


def build_lexical_resource_feedback_prompt(
    essay_structure: Dict[str, Any],
    lr_evidence: Dict[str, Any],
) -> List[Dict[str, str]]:
    es = json.dumps(
        essay_structure, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    ev = json.dumps(
        lr_evidence, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )

    system = {
        "role": "system",
        "content": """
You are an IELTS Writing examiner focusing ONLY on LEXICAL RESOURCE (LR).

You will score ONLY LR using:
- essay_structure (ONLY for underlength guardrails if needed)
- lr_evidence (auditable evidence extracted in Stage B)

CRITICAL RULES:
1) Base your judgment ONLY on lr_evidence (+ word_count from essay_structure if relevant).
   Do NOT invent evidence. Do NOT infer beyond provided evidence.
2) Do NOT score TR/CC/GRA. LR only.
3) Use the OFFICIAL LR band descriptors (Bands 1–9) provided below to select the score.
4) You may use .5 increments ONLY for clear borderline cases between two adjacent bands.
5) Feedback must be concise and examiner-style (not sentence-by-sentence debugging).
6) You may cite at most 1–2 sentence ids total in feedback (optional).

OFFICIAL LR BAND ANCHORS (Task 2):
Band 9:
- Full flexibility and precise use; wide range used accurately and appropriately; very natural and sophisticated control.
- Minor spelling/word formation errors are extremely rare and minimal impact.
Band 8:
- Wide resource used fluently and flexibly to convey precise meanings.
- Skillful uncommon/idiomatic items when appropriate, occasional inaccuracies in word choice/collocation.
- Occasional spelling/word formation errors with minimal impact.
Band 7:
- Sufficient resource for some flexibility and precision.
- Some ability to use less common/idiomatic items.
- Awareness of style and collocation, though inappropriacies occur.
- Few spelling/word formation errors, not detracting from clarity.
Band 6:
- Generally adequate and appropriate.
- Meaning generally clear despite restricted range or lack of precision.
- Some spelling/word formation errors but do not impede communication.
Band 5:
- Limited but minimally adequate; simple vocab accurate but little variation; frequent simplification/repetition.
- Frequent lapses in appropriacy; spelling/formation errors noticeable and may cause difficulty.
Band 4:
- Limited and inadequate/unrelated; basic repetitive vocab; inappropriate chunks/formulaic language.
- Inappropriate word choice / formation / spelling may impede meaning.
Band 3:
- Inadequate resource; possible over-dependence on memorised language; errors predominate and may severely impede meaning.
Band 2:
- Extremely limited with few recognisable strings; no apparent control of formation/spelling.
Band 1:
- <=20 words OR no resource apparent except isolated words.

BAND SELECTION PROCEDURE (must follow):
Step 1) Check severe constraints:
- If essay is extremely underlength (word_count very low), consider lower bands consistent with descriptors.
Step 2) Pick closest anchor band using lr_evidence.summaries and the distribution of:
- repetition (range)
- vocabulary_highlights (range/precision/collocation sophistication)
- lexical_errors (type + severity + impact)
Step 3) Adjust by +/-0.5 only if clearly borderline.

CAP GUIDANCE (to stabilize scoring):
- If summaries.error_impact_overall is "impedes" OR many errors have impact="impedes" -> LR cannot exceed Band 5.
- If summaries.range_level is "limited" with frequent repetition AND precision_level="low" -> LR cannot exceed Band 5/6.
- If range_level="wide" AND precision_level="high" AND error_density="low" -> LR is likely Band 8+ unless evidence contradicts.

OUTPUT JSON ONLY. No markdown. No extra keys. Must match schema exactly:
{
  "lr_band": 0.0,
  "band_anchor": "9|8|7|6|5|4|3|2|1",
  "feedback": {
    "summary": "string",
    "strengths": ["string","string"],
    "weaknesses": ["string"],
    "next_step": "string"
  }
}

Feedback constraints:
- strengths exactly 2, weaknesses exactly 1, next_step exactly 1
- Keep feedback actionable for later rewrite (makeup).
""".strip(),
    }

    user = {
        "role": "user",
        "content": f"""
essay_structure:
{es}

lr_evidence:
{ev}
""".strip(),
    }

    return [system, user]
