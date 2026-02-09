from typing import Any, Dict, Optional

from admitplus.api.exams.exam_attempt_service import AttemptService
from admitplus.api.exams.exam_evaluation_service import ExamFeedbackService
from admitplus.api.exams.exam_attempt_schema import (
    AttemptCreateRequest,
    AttemptMetadata,
    StudentAnswer,
)
from admitplus.api.exams.exam_task_repo import ExamTaskVectorRepo

attempt_service = AttemptService()
exam_evaluation_service = ExamFeedbackService()
exam_task_vector_repo = ExamTaskVectorRepo()


async def generate_writing_scoring_and_feedback(attempt_id: str) -> Dict[str, Any]:
    """
    Generate IELTS writing score and feedback for a specific attempt.

    Args:
        attempt_id (str): The unique identifier of the writing attempt whose
            score and feedback should be generated.

    Returns:
        dict: A tool-friendly response with the following keys:

            - ``status`` (str): ``"success"`` if the scoring completed,
              otherwise ``"error"``.
            - ``result`` (dict | None): On success, the raw scoring and
              feedback payload returned from ``generate_feedback_v2``, which
              includes overall score, per-criterion feedback, and overall
              feedback text. ``None`` on error.
            - ``error_message`` (str | None): A human-readable explanation
              when ``status`` is ``"error"``, otherwise ``None``.
    """
    try:
        feedback = await exam_evaluation_service.generate_feedback_v2(attempt_id)
        return {
            "status": "success",
            "result": feedback,
            "error_message": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "result": None,
            "error_message": str(exc),
        }


async def get_writing_scoring_and_feedback(
    attempt_id: str, student_id: str
) -> Dict[str, Any]:
    """
    Retrieve existing IELTS writing scoring and feedback for an attempt.

    Args:
        attempt_id (str): The unique identifier of the writing attempt.
        student_id (str): The ID of the student requesting their feedback.

    Returns:
        dict: A tool-friendly response with the following keys:

            - ``status`` (str): ``"success"`` if feedback was retrieved,
              otherwise ``"error"``.
            - ``feedback_items`` (list | None): A list of feedback objects
              (converted to dictionaries) when successful; ``None`` on error.
            - ``total`` (int | None): Total number of feedback entries when
              successful; ``None`` on error.
            - ``error_message`` (str | None): A human-readable explanation
              when ``status`` is ``"error"``, otherwise ``None``.
    """
    try:
        feedback_list = await exam_evaluation_service.list_feedbacks(
            attempt_id=attempt_id, student_id=student_id
        )

        # Pydantic model -> dict
        if hasattr(feedback_list, "model_dump"):
            feedback_dict = feedback_list.model_dump(mode="json", exclude_none=True)
        else:
            feedback_dict = {
                "items": [],
                "total": 0,
            }

        return {
            "status": "success",
            "feedback_items": feedback_dict.get("items", []),
            "total": feedback_dict.get("total", 0),
            "error_message": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "feedback_items": None,
            "total": None,
            "error_message": str(exc),
        }


async def create_writing_submission(
    student_id: str,
    task_id: str,
    student_answer_text: str,
    mode: str = "practice",
    time_spent_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a new IELTS writing attempt (submission) for a student.

    Use this when the student submits a new piece of writing. Pass the task/prompt
    ID and the student's written content. For writing tasks, student_answer_text
    is the essay or response body.

    Args:
        student_id (str): The ID of the student creating the writing attempt.
        task_id (str): The task or prompt ID this attempt is for (e.g. from
            task_agent's selected_prompt_id).
        student_answer_text (str): The student's written answer (essay or
            response text).
        mode (str, optional): Attempt mode; use "practice" or "exam". Defaults
            to "practice".
        time_spent_seconds (int, optional): Time spent on the attempt in seconds.

    Returns:
        dict: A tool-friendly response with the following keys:

            - ``status`` (str): ``"success"`` if the attempt was created,
              otherwise ``"error"``.
            - ``attempt`` (dict | None): The created attempt object as a
              dictionary when successful; ``None`` on error.
            - ``error_message`` (str | None): A human-readable explanation
              when ``status`` is ``"error"``, otherwise ``None``.
    """
    try:
        student_answer = StudentAnswer(text=student_answer_text)
        metadata = (
            AttemptMetadata(time_spent_seconds=time_spent_seconds)
            if time_spent_seconds is not None
            else None
        )
        attempt_request = AttemptCreateRequest(
            task_id=task_id,
            mode=mode,
            student_answer=student_answer,
            metadata=metadata,
        )
        attempt = await attempt_service.create_attempt(student_id, attempt_request)
        if hasattr(attempt, "model_dump"):
            attempt_dict = attempt.model_dump(mode="json", exclude_none=True)
        else:
            attempt_dict = attempt

        return {
            "status": "success",
            "attempt": attempt_dict,
            "error_message": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "attempt": None,
            "error_message": str(exc),
        }


async def search_writing_prompts_by_embedding(
    query_vector: list[float],
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Search IELTS writing prompts using vector similarity in Milvus.

    Args:
        query_vector (list[float]): The embedding vector representing the
            user's intent or writing topic. This is passed as ``query["vector"]``
            to the underlying Milvus search.
        limit (int, optional): Maximum number of similar prompts to return.
            Defaults to 5.

    Returns:
        dict: A tool-friendly response with the following keys:

            - ``status`` (str): ``"success"`` if the search completed,
              otherwise ``"error"``.
            - ``results`` (Any | None): The raw search results returned from
              ``ExamTaskVectorRepo.search_exam`` when successful; ``None`` on
              error.
            - ``error_message`` (str | None): A human-readable explanation
              when ``status`` is ``"error"``, otherwise ``None``.
    """
    try:
        query: Dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
        }
        results = await exam_task_vector_repo.search_exam(query)
        return {
            "status": "success",
            "results": results,
            "error_message": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "results": None,
            "error_message": str(exc),
        }


# async def search_similar_writing_issues():
#     pass
