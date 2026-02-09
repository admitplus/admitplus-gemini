def build_revision_prompt(input_data: dict) -> list:
    ws = input_data.get("writing_settings", {})
    cons = input_data.get("constraints", {})

    system_prompt = f"""
You are a precise admissions essay editor.
Revise ONLY the selected passage while preserving the student's authentic voice, facts, and narrative intent.

Editing rules:
- Follow the specified template: {ws.get("structure_template", "STAR")} when applicable.
- Maintain tone: {ws.get("tone", "Reflective")}; perspective: {ws.get("narrative_perspective", "First Person")}; language: {ws.get("language_preference", "American English")}.
- Keep changes within a ~{int(cons.get("max_change_ratio", 0.6) * 100)}% edit scope unless required for clarity.
- Respect word target for the section (~{cons.get("word_limit_section", "N/A")} words).
- Do NOT invent new facts; use only provided factual materials and original text.
- Preserve required phrases: {", ".join(cons.get("must_keep_phrases", [])) or "None"}.
- Avoid: {", ".join(cons.get("must_avoid", [])) or "None"}.
- Ensure smooth transitions to preceding and following text.
Output policy:
- If return_format=section_only → output the REVISED SECTION TEXT only.
- If return_format=full_essay → output the FULL ESSAY with only this section changed.
- If return_format=section_plus_changelog → output:
  1) REVISED SECTION
  2) CHANGELOG: bullet points explaining key edits (clarity, structure, tone, evidence).
No headings, no Markdown unless 'section_plus_changelog' is requested.
""".strip()

    # --- Build users content ---
    guidance = "\n".join([f"- {g}" for g in input_data.get("user_guidance", [])])
    materials = "\n".join([f"{m}" for m in input_data.get("factual_materials", [])])

    user_prompt = f"""
MODE: {input_data.get("mode", "section")}
RETURN_FORMAT: {input_data.get("return_format", "section_only")}

SELECTED SECTION ({input_data.get("selected", {}).get("label", "Unnamed")}):
{input_data.get("selected", {}).get("text", "").strip()}

PRECEDING TEXT (for transition):
{(input_data.get("context", {}) or {}).get("preceding_text", "").strip()}

FOLLOWING TEXT (for transition):
{(input_data.get("context", {}) or {}).get("following_text", "").strip()}

FULL ESSAY (reference only):
{(input_data.get("context", {}) or {}).get("full_essay", "").strip()}

USER GUIDANCE (apply faithfully):
{guidance}

FACTUAL MATERIALS (may cite/reinforce; do not invent beyond these and the original text):
{materials}

TASK:
Rewrite the selected section to implement the guidance, keep facts accurate, maintain the specified tone/perspective, and fit the target length. Ensure the revised section connects naturally with the surrounding text.
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
