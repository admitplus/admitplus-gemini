import json
import logging
from typing import Any, Callable, Awaitable, List, Dict

from admitplus.llm.prompts.gpt_prompts.ielts_writing.task_1_achievement_prompt import (
    build_task_1_spec_inference_prompt,
    build_task_1_extracting_auditable_evidence_prompt,
)
from admitplus.llm.prompts.gpt_prompts.ielts_writing.task_2_response_prompt import (
    build_task_response_feedback_prompt,
    build_task_2_spec_inference_prompt,
    build_task_2_extracting_auditable_evidence_prompt,
)
from admitplus.llm.providers.openai.openai_client import generate_text


async def _call_openai_json(
    messages: List[Dict[str, str]], log_label: str | None = None
) -> Any:
    """
    Call OpenAI chat completion and parse JSON response.

    This helper is async and must be awaited.
    """
    raw = await generate_text(messages)
    if log_label:
        logging.info(
            f"[ExamEvalUtils] [{log_label}] Received LLM response with {len(raw)} characters"
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logging.error(
            f"[ExamEvalUtils] [{log_label or 'unknown'}] Failed to parse JSON response: {str(e)}"
        )
        raise


async def _run_task_pipeline(
    essay_structure: dict,
    get_spec_prompt: Callable[[], List[Dict[str, str]]],
    get_evidence_prompt: Callable[[dict], List[Dict[str, str]]],
) -> dict:
    """
    Stage A: task spec inference → Stage B: evidence extraction → Stage C: band mapping.
    """
    spec = await _call_openai_json(get_spec_prompt(), "task_spec_inference")
    evidence = await _call_openai_json(
        get_evidence_prompt(spec), "task_auditable_evidence"
    )
    feedback = await _call_openai_json(
        build_task_response_feedback_prompt(spec, essay_structure, evidence),
        "task_response_score",
    )
    return feedback or {}


async def run_task_feedback_pipeline(
    task_type: str, essay_prompt: str, essay_structure: dict
) -> dict | None:
    """
    Run the end-to-end task response feedback pipeline for Task 1 / Task 2.
    """
    if not task_type:
        logging.warning(
            "[ExamEvalUtils] [TaskPipeline] Missing task_type; skipping task feedback."
        )
        return None

    if task_type == "task_1":
        return await _run_task_pipeline(
            essay_structure,
            get_spec_prompt=lambda: build_task_1_spec_inference_prompt(
                essay_prompt, "image_text"
            ),
            get_evidence_prompt=lambda spec: build_task_1_extracting_auditable_evidence_prompt(
                spec, essay_structure, "image_text"
            ),
        )
    if task_type == "task_2":
        return await _run_task_pipeline(
            essay_structure,
            get_spec_prompt=lambda: build_task_2_spec_inference_prompt(essay_prompt),
            get_evidence_prompt=lambda spec: build_task_2_extracting_auditable_evidence_prompt(
                spec, essay_structure
            ),
        )

    logging.warning(
        f"[ExamEvalUtils] [TaskPipeline] Unsupported task_type='{task_type}'; skipping task feedback."
    )
    return None


def round_to_half(x: float) -> float:
    """
    Round to the nearest 0.5 (IELTS-style half-band rounding).
    """
    return round(x * 2) / 2


def overall_band(tr: float, cc: float, lr: float, gra: float) -> float:
    """
    Compute overall writing band from 4 criteria.
    """
    avg = (tr + cc + lr + gra) / 4.0
    return round_to_half(avg)


async def _run_criterion_pipeline(
    essay_structure: dict,
    build_evidence_prompt,
    build_feedback_prompt,
    log_label: str,
) -> dict:
    """
    Evidence extraction → feedback for one criterion (CC / LR / GRA).
    """
    evidence = await _call_openai_json(
        build_evidence_prompt(essay_structure), f"{log_label}_evidence"
    )
    feedback = await _call_openai_json(
        build_feedback_prompt(essay_structure, evidence), log_label=log_label
    )
    return feedback or {}
