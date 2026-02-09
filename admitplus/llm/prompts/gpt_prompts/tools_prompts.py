from typing import List, Dict


def build_parser_university_type(student_input):
    return [
        {
            "role": "system",
            "content": f"""
                Input is about returning university type, maybe ["public"] or ["private"] or ["public", "private"]
                return 
            """,
        }
    ]


def build_location_parser_prompt(student_input: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a study abroad advising assistant. "
                "Your job is to extract geographic location preferences from the students's natural language input. "
                "Return structured results in JSON format with the following fields:\n"
                "- states: list of U.S. states mentioned or implied\n"
                "- regions: list of U.S. regions (west, east, south, midwest)\n"
                "- cities: list of city names mentioned or implied"
            ),
        },
        {
            "role": "user",
            "content": (
                "Please extract structured location preferences from the following sentences.\n\n"
                "Input: I want to study in California or somewhere in the west coast.\n"
                "Output:\n"
                "```json\n"
                "{\n"
                '  "states": ["California"],\n'
                '  "regions": ["west"],\n'
                '  "cities": []\n'
                "}\n"
                "```\n\n"
                "Input: I'm looking for schools in New York City or Boston.\n"
                "Output:\n"
                "```json\n"
                "{\n"
                '  "states": ["New York", "Massachusetts"],\n'
                '  "regions": ["east"],\n'
                '  "cities": ["New York", "Boston"]\n'
                "}\n"
                "```\n\n"
                "Input: I’d love to be somewhere warm like Florida, or maybe near Los Angeles.\n"
                "Output:\n"
                "```json\n"
                "{\n"
                '  "states": ["Florida", "California"],\n'
                '  "regions": ["south", "west"],\n'
                '  "cities": ["Los Angeles"]\n'
                "}\n"
                "```\n\n"
                f"Now extract the location preferences from the following sentence:\n\n"
                f"Input: {student_input}\n"
                f"Output:"
            ),
        },
    ]


def build_multi_language_parser_prompt(student_input: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an assistant that extracts English test results from users input.\n"
                "Supported tests: TOEFL, IELTS, Duolingo.\n"
                "Since students typically only take one language test, return only the first or most relevant test found.\n"
                "Return a JSON object with fields: 'type' and 'score'.\n"
                "Score should be int (TOEFL/Duolingo) or float (IELTS).\n"
                "If no test or score is found, return null."
            ),
        },
        {
            "role": "user",
            "content": f"""
Extract the English test score from the following input:

\"{student_input}\"

Return result like this:
```json
{{ "type": "TOEFL", "score": 106 }}
```
""",
        },
    ]


def build_gpa_parser_prompt(student_input: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that extracts GPA from a students's input.\n"
                "The GPA should be normalized to a 4.0 scale. \n"
                "If the students provides a percentage score (e.g., 85, 92, 78.5), you should convert it to a GPA using this reference:\n\n"
                "- 90–100 → 4.0\n"
                "- 85–89 → 3.7\n"
                "- 80–84 → 3.3\n"
                "- 75–79 → 3.0\n"
                "- 70–74 → 2.7\n"
                "- 60–69 → 2.0\n"
                "- Below 60 → 0.0\n\n"
                "If the students gives GPA directly (e.g., 'My GPA is 3.6'), just use it.\n"
                "If no score or GPA is mentioned, return null.\n\n"
                "Output format:\n"
                "```json\n"
                '{ "gpa": 3.7 }\n'
                "```\n"
                "or\n"
                "```json\n"
                "null\n"
                "```"
            ),
        },
        {
            "role": "user",
            "content": f"""
Extract the GPA from the following input and normalize it to a 4.0 scale:

"{student_input}"
""",
        },
    ]


def build_sat_parser_prompt(student_input: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that extracts SAT score from a students's input.\n"
                "The SAT score should be between 400-1600.\n"
                "If the students provides a percentage score or other format, convert it appropriately.\n"
                "If no SAT score is mentioned, return null.\n\n"
                "Output format:\n"
                "```json\n"
                '{ "sat": 1400 }\n'
                "```\n"
                "or\n"
                "```json\n"
                "null\n"
                "```"
            ),
        },
        {
            "role": "user",
            "content": f"""
Extract the SAT score from the following input:

"{student_input}"
""",
        },
    ]


def build_budget_parser_prompt(student_input: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that extracts annual budget from a students's input.\n"
                "The budget should be in USD dollars per year.\n"
                "If the students provides a monthly amount, multiply by 12.\n"
                "If the students provides a total amount for 4 years, divide by 4.\n"
                "If no budget is mentioned, return null.\n\n"
                "Output format:\n"
                "```json\n"
                '{ "budget": 50000 }\n'
                "```\n"
                "or\n"
                "```json\n"
                "null\n"
                "```"
            ),
        },
        {
            "role": "user",
            "content": f"""
Extract the annual budget from the following input:

"{student_input}"
""",
        },
    ]
