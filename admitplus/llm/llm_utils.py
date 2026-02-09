import json
import logging
import re
from typing import Dict, Any


def parse_llm_json_response(llm_response: str, context: str = "") -> Dict[str, Any]:
    json_str = llm_response.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Fallback: try to extract JSON object if LLM didn't follow instructions
        log_prefix = context if context else "[LLMUtils]"
        logging.warning(
            f"{log_prefix} Failed to parse JSON directly, attempting extraction"
        )

        json_match = re.search(r"\{.*\}", json_str, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logging.error(f"{log_prefix} Failed to parse JSON: {str(e)}")
        logging.error(f"{log_prefix} Response content: {llm_response[:500]}")
        raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
