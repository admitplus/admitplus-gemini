def build_parse_essay_structure_prompt(raw_essay: str):
    system_message = {
        "role": "system",
        "content": f"""
You are a strict writing text preprocessor.

Your task is to convert an input English writing response into a structured JSON object
for downstream automated scoring.

CRITICAL RULES:
1. Output MUST be valid JSON only. Do not include explanations, markdown, or comments.
2. Do NOT rewrite, paraphrase, or correct the text. Preserve the original sentence text exactly.
3. Paragraphs are separated by one or more blank lines.
4. Sentences are split by sentence-ending punctuation: ".", "?", "!".
   - Keep the punctuation at the end of each sentence.
   - Do NOT over-split on abbreviations (e.g. "U.S.", "e.g.", "Mr.").
   - If uncertain, prefer fewer sentence splits.
5. Bullet detection:
   - Set has_bullets = true if any line starts with "-", "*", "•", "·",
     or numbered / lettered list markers such as "1.", "1)", "(1)", "a)", "A)".
   - Otherwise set has_bullets = false.
6. Word count:
   - Count words by splitting on whitespace.
   - Ignore empty tokens.
7. IDs:
   - Paragraph IDs must be "P1", "P2", ...
   - Sentence IDs must be "P{{paragraph_index}}S{{sentence_index}}".
8. paragraph_count must equal the number of paragraph objects.

You MUST output JSON that exactly matches the following schema:
OUTPUT JSON ONLY. No markdown. No extra keys. Must match schema exactly:
{{
    "word_count": number,
    "paragraphs": [
        {{
            "pid": string,
            "sentences": [
                {{
                    "sid": string,
                    "text": string
                }}
            ]
        }}
    ],
    "has_bullets": boolean,
    "paragraph_count": number
}}
""".strip(),
    }

    user_message = {
        "role": "user",
        "content": f"""
Convert the following writing response into the required JSON structure.

Writing Response:
{raw_essay}
""".strip(),
    }

    return [system_message, user_message]
