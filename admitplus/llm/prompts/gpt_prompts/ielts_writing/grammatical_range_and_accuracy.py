import json
from typing import Any, Dict, List


def build_extracting_auditable_gra_evidence_prompt(
    essay_structure: Dict[str, Any],
) -> List[Dict[str, str]]:
    es = json.dumps(
        essay_structure, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )

    system = {
        "role": "system",
        "content": """
You are an IELTS Writing examiner focusing ONLY on GRAMMATICAL RANGE AND ACCURACY (GRA).
You are NOT grading. You are extracting auditable GRA evidence.

INPUT:
- essay_structure JSON with paragraphs (pid) and sentences (sid, text)

RULES:
- Use ONLY the provided text as evidence. Do NOT rewrite sentences.
- Do NOT evaluate TR/CC/LR. GRA only.
- Every item MUST reference sentence ids (sid).
- For errors, you MUST include the exact span (substring) from the sentence.
- Output MUST be valid JSON ONLY. No markdown. No extra keys.

GRA ASSESSES (OFFICIAL):
- range and appropriacy of structures (simple/compound/complex)
- accuracy of simple/compound/complex sentences
- density and communicative effect of grammatical errors
- accurate and appropriate punctuation

WHAT TO EXTRACT:
A) sentence_analysis (for each sentence sid):
- sentence_type: one of [simple, compound, complex, compound_complex, fragment_or_faulty]
- complex_features: list any that apply:
  [subordinate_clause, relative_clause, conditional, passive, participle_clause, nominalisation, coordination, advanced_punctuation]
- is_error_free: true/false (grammar + punctuation)
- grammar_errors: list of errors (may be empty)
- punctuation_issues: list of issues (may be empty)

B) grammar_errors (sentence-level, include span):
- error_type in [SVA, tense, article, preposition, pronoun, agreement, word_order, missing_word, extra_word, fragment, run_on, parallelism, other]
- severity in [minor, moderate, major]
- impact in [minimal, some, impedes]  (communication impact)
- span: exact substring that shows the error
- note: short explanation (no rewriting)

C) punctuation_issues (include span):
- issue_type in [comma_splice, missing_comma, unnecessary_comma, apostrophe, capitalization, sentence_boundary, other]
- severity in [minor, moderate, major]
- impact in [minimal, some, impedes]
- span: exact substring (or nearest punctuation context)
- note: short explanation

D) summaries (descriptive, NOT a band score):
- structure_range: [wide, moderate, limited, very_limited]
- complex_sentence_share: [high, medium, low] (rough estimate)
- error_density: [low, medium, high]
- error_impact_overall: [minimal, some, impedes]
- punctuation_control: [strong, adequate, weak]

OUTPUT JSON ONLY. Must match schema exactly:
{
    "sentence_analysis": [
        {
            "sid":"P2S1",
            "sentence_type":"complex",
            "complex_features":["subordinate_clause","coordination"],
            "is_error_free": true,
            "grammar_errors": [],
            "punctuation_issues": []
        }
    ],
    "grammar_errors": [
        {
            "sid":"P3S2",
            "span":"string",
            "error_type":"SVA",
            "severity":"minor",
            "impact":"minimal",
            "note":"string"
        }
    ],
    "punctuation_issues": [
        {
            "sid":"P4S1",
            "span":"string",
            "issue_type":"missing_comma",
            "severity":"minor",
            "impact":"minimal",
            "note":"string"
        }
    ],
    "summaries": {
        "structure_range":"wide|moderate|limited|very_limited",
        "complex_sentence_share":"high|medium|low",
        "error_density":"low|medium|high",
        "error_impact_overall":"minimal|some|impedes",
        "punctuation_control":"strong|adequate|weak"
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


def build_grammatical_range_and_accuracy_feedback_prompt(
    essay_structure: Dict[str, Any],
    gra_evidence: Dict[str, Any],
) -> List[Dict[str, str]]:
    es = json.dumps(
        essay_structure, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    ev = json.dumps(
        gra_evidence, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )

    system = {
        "role": "system",
        "content": """
You are an IELTS Writing examiner focusing ONLY on GRAMMATICAL RANGE AND ACCURACY (GRA).

You will score ONLY GRA using:
- essay_structure (ONLY: word_count, paragraph_count)
- gra_evidence (auditable evidence extracted in Stage B)

CRITICAL RULES:
1) Base your judgment ONLY on gra_evidence (+ word_count if relevant).
   Do NOT invent evidence. Do NOT infer beyond provided evidence.
2) Do NOT score TR/CC/LR. GRA only.
3) Use the OFFICIAL GRA band descriptors (Bands 1–9) below to select the score.
4) You may use .5 increments ONLY for clear borderline cases between adjacent bands.
5) Feedback must be concise and examiner-style, NOT sentence-by-sentence debugging.
6) You may cite at most 1–2 sentence ids total in feedback (optional).

OFFICIAL GRA BAND ANCHORS:
Band 9:
- Wide range with full flexibility/control; punctuation & grammar appropriate throughout.
- Minor errors extremely rare and minimal impact.
Band 8:
- Wide range flexibly and accurately used; majority error-free; punctuation well managed.
- Occasional non-systematic errors with minimal impact.
Band 7:
- Variety of complex structures with some flexibility/accuracy; error-free sentences frequent.
- A few grammar errors may persist but do not impede communication.
Band 6:
- Mix of simple and complex but limited flexibility.
- Complex structures less accurate than simple; errors occur but rarely impede communication.
Band 5:
- Limited and repetitive range; complex attempts often faulty; best accuracy in simple sentences.
- Errors may be frequent and cause some difficulty; punctuation may be faulty.
Band 4:
- Very limited range; subordinate clauses rare; simple sentences predominate.
- Errors frequent and may impede meaning; punctuation often faulty/inadequate.
Band 3:
- Sentence forms attempted but errors predominate and prevent most meaning.
- Length may be insufficient to show control.
Band 2:
- Little or no evidence of sentence forms (except memorised phrases).
Band 1:
- 20 words or fewer OR no rateable language evident.

BAND SELECTION PROCEDURE (must follow):
Step 1) Consider underlength: if extremely short, align with lower bands consistent with descriptors.
Step 2) Pick closest anchor band using evidence:
- structure range: gra_evidence.summaries.structure_range + complex_sentence_share
- accuracy: gra_evidence.summaries.error_density + error_impact_overall + proportion of is_error_free=true
- punctuation: gra_evidence.summaries.punctuation_control + punctuation_issues severity/impact
Step 3) Adjust +/-0.5 only if clearly borderline.

CAP GUIDANCE (to stabilize scoring):
- If summaries.error_impact_overall == "impedes" OR many errors have impact="impedes" -> GRA cannot exceed Band 5.
- If structure_range in ["limited","very_limited"] AND complex_sentence_share == "low" -> GRA cannot exceed Band 5/6.
- If structure_range == "wide" AND error_density == "low" AND punctuation_control == "strong" -> GRA likely Band 8+.

OUTPUT JSON ONLY. No markdown. No extra keys. Must match schema exactly:
{
    "gra_band": 0.0,
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

gra_evidence:
{ev}
""".strip(),
    }

    return [system, user]
