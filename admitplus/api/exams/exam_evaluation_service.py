import asyncio
import logging
import os
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, Any

from fastapi import HTTPException

from .exam_attempt_repo import ExamAttemptRepo
from .exam_evaluaion_utils import (
    _call_openai_json,
    run_task_feedback_pipeline,
    _run_criterion_pipeline,
    overall_band,
)
from .exam_evaluation_repo import ExamFeedbackRepo
from .exam_evaluation_schema import (
    FeedbackResponse,
    ScoreDetail,
    FeedbackListResponse,
    ScoreSubscoresDetail,
    ScoreWithSubscoresDetail,
    ModelEssayInfo,
    RevisionSuggestion,
)
from admitplus.utils.crypto_utils import generate_uuid
from admitplus.llm.llm_utils import parse_llm_json_response
from admitplus.llm.providers.openai.openai_client import (
    generate_text,
    extract_text_from_image,
)
from admitplus.llm.prompts.gpt_prompts.exam_prompt.ielts.writing_evaluation_prompt import (
    build_ielts_writing_evaluation_prompt,
)
from admitplus.llm.prompts.gpt_prompts.exam_prompt.ielts.generate_model_essay_prompt import (
    build_model_essay_prompt,
)
from .exam_model import FeedbackTypeEnum, get_score_scale
from ...llm.prompts.gpt_prompts.ielts_writing.coherence_and_cohesion_prompt import (
    build_extracting_auditable_cc_evidence_prompt,
    build_coherence_and_cohesion_feedback_prompt,
)
from ...llm.prompts.gpt_prompts.ielts_writing.grammatical_range_and_accuracy import (
    build_extracting_auditable_gra_evidence_prompt,
    build_grammatical_range_and_accuracy_feedback_prompt,
)
from ...llm.prompts.gpt_prompts.ielts_writing.lexical_resource_prompt import (
    build_extracting_auditable_lr_evidence_prompt,
    build_lexical_resource_feedback_prompt,
)
from ...llm.prompts.gpt_prompts.ielts_writing.overall_feedback_prompt import (
    build_overall_feedback_prompt,
)
from ...llm.prompts.gpt_prompts.ielts_writing.parse_essay_structure_prompt import (
    build_parse_essay_structure_prompt,
)


class ExamFeedbackService:
    def __init__(self):
        self.attempt_repo = ExamAttemptRepo()
        self.feedback_repo = ExamFeedbackRepo()

    async def _build_feedback_response(
        self,
        feedback_doc: dict,
        attempt_id: str,
        attempt_doc: dict = None,
        created_at_value: datetime = None,
    ) -> FeedbackResponse:
        """Build feedback response from document based on feedback type"""
        feedback_id = feedback_doc.get("feedback_id") or feedback_doc.get("id", "")
        feedback_type = feedback_doc.get("feedback_type", FeedbackTypeEnum.AI.value)

        # Common fields
        response_data = {
            "feedback_id": feedback_id,
            "attempt_id": attempt_id,
            "feedback_type": feedback_type,
            "created_at": created_at_value or feedback_doc.get("created_at"),
        }

        # Build response based on feedback type
        if feedback_type == FeedbackTypeEnum.AI.value:
            score_data = feedback_doc.get("score", {})
            subscores_data = score_data.get("subscores", {})

            # Get exam and section from attempt to determine scale
            if attempt_doc:
                exam = attempt_doc.get("exam", "").lower()
                section = attempt_doc.get("section", "").lower()
                scale = score_data.get("scale", get_score_scale(exam, section))
            else:
                scale = score_data.get("scale")

            overall_score = score_data.get("overall", 0.0)

            # Extract subscore data
            task_response_data = subscores_data.get("task_response", {})
            coherence_cohesion_data = subscores_data.get("coherence_cohesion", {})
            lexical_resource_data = subscores_data.get("lexical_resource", {})
            grammar_data = subscores_data.get("grammar", {})

            # Check if new structure (dict with score and reason) or old structure (just float)
            if isinstance(task_response_data, dict) and "score" in task_response_data:
                # New structure with score and reason
                subscores = ScoreSubscoresDetail(
                    task_response=ScoreDetail(
                        score=task_response_data.get("score", 0.0),
                        reason=task_response_data.get("reason", ""),
                    ),
                    coherence_cohesion=ScoreDetail(
                        score=coherence_cohesion_data.get("score", 0.0),
                        reason=coherence_cohesion_data.get("reason", ""),
                    ),
                    lexical_resource=ScoreDetail(
                        score=lexical_resource_data.get("score", 0.0),
                        reason=lexical_resource_data.get("reason", ""),
                    ),
                    grammar=ScoreDetail(
                        score=grammar_data.get("score", 0.0),
                        reason=grammar_data.get("reason", ""),
                    ),
                )
            else:
                # Old structure (backward compatibility) - subscores are just float values
                grammar_score = subscores_data.get(
                    "grammar", subscores_data.get("grammatical_range_and_accuracy", 0.0)
                )
                subscores = ScoreSubscoresDetail(
                    task_response=ScoreDetail(
                        score=subscores_data.get("task_response", 0.0)
                        if isinstance(subscores_data.get("task_response"), (int, float))
                        else 0.0,
                        reason="",
                    ),
                    coherence_cohesion=ScoreDetail(
                        score=subscores_data.get("coherence_and_cohesion", 0.0)
                        if isinstance(
                            subscores_data.get("coherence_and_cohesion"), (int, float)
                        )
                        else 0.0,
                        reason="",
                    ),
                    lexical_resource=ScoreDetail(
                        score=subscores_data.get("lexical_resource", 0.0)
                        if isinstance(
                            subscores_data.get("lexical_resource"), (int, float)
                        )
                        else 0.0,
                        reason="",
                    ),
                    grammar=ScoreDetail(
                        score=grammar_score
                        if isinstance(grammar_score, (int, float))
                        else 0.0,
                        reason="",
                    ),
                )

            # Parse suggestions if present
            suggestions = None
            suggestions_data = feedback_doc.get("suggestions", [])
            if suggestions_data:
                suggestions = [
                    RevisionSuggestion(
                        original_text=s.get("original_text", ""),
                        suggested_text=s.get("suggested_text", ""),
                        category=s.get("category", ""),
                        explanation=s.get("explanation", ""),
                    )
                    for s in suggestions_data
                ]

            response_data.update(
                {
                    "model_version": feedback_doc.get("model_version", ""),
                    "score": ScoreWithSubscoresDetail(
                        overall=overall_score, subscores=subscores, scale=scale
                    ),
                    "summary": feedback_doc.get("summary", ""),
                    "ai_comment": feedback_doc.get("ai_comment", ""),
                    "suggestions": suggestions,
                }
            )
        elif feedback_type == FeedbackTypeEnum.MANUAL.value:
            response_data["teacher_comment"] = feedback_doc.get("teacher_comment", "")
        else:
            logging.warning(
                f"[ExamFeedbackService] [BuildFeedbackResponse] Unknown feedback type: {feedback_type}, feedback_id={feedback_id}"
            )

        return FeedbackResponse(**response_data)

    def _extract_attempt_data(self, attempt_doc: dict) -> dict:
        """Extract and validate data from attempt document"""
        exam = attempt_doc.get("exam", "").lower()
        section = attempt_doc.get("section", "").lower()
        task_type = attempt_doc.get("task_type", "").lower()
        student_answer_data = attempt_doc.get("student_answer", {}) or {}

        task_prompt_data = attempt_doc.get("task_prompt", {}) or {}
        if not task_prompt_data:
            raise ValueError(
                f"Task prompt not found in attempt: {attempt_doc.get('attempt_id', 'unknown')}"
            )

        return {
            "exam": exam,
            "section": section,
            "task_type": task_type,
            "student_answer": student_answer_data,
            "task_prompt": task_prompt_data,
            "description": task_prompt_data.get("description", ""),
            "input_assets": task_prompt_data.get("input_assets", {}) or {},
        }

    async def _process_image_extraction(
        self, input_assets_data: dict, attempt_id: str
    ) -> dict:
        """
        Process input assets for feedback generation.

        Note: For attempts created after the update, image_text is already stored.
        This method handles backward compatibility for old attempts that may still have image_url.
        """
        if not input_assets_data:
            return input_assets_data

        # If image_text is already present (new attempts), use it directly
        if input_assets_data.get("image_text"):
            logging.debug(
                f"[ExamFeedbackService] [GenerateFeedback] Using stored image_text - attempt_id={attempt_id}"
            )
            return input_assets_data

        # Backward compatibility: extract from image_url if present (old attempts)
        if input_assets_data.get("image_url"):
            image_url = input_assets_data.get("image_url")
            try:
                logging.info(
                    f"[ExamFeedbackService] [GenerateFeedback] Extracting text from image (backward compatibility) - attempt_id={attempt_id}"
                )
                extracted_image_text = await extract_text_from_image(image_url)
                input_assets_data = input_assets_data.copy()
                input_assets_data["image_text"] = extracted_image_text
                logging.info(
                    f"[ExamFeedbackService] [GenerateFeedback] Successfully extracted {len(extracted_image_text)} characters from image"
                )
            except Exception as e:
                logging.warning(
                    f"[ExamFeedbackService] [GenerateFeedback] Failed to extract text from image: {str(e)}. Continuing without image text extraction."
                )

        return input_assets_data

    def _parse_llm_feedback_response(self, feedback_data: dict) -> dict:
        """Parse LLM response and extract all feedback components"""
        score_data = feedback_data.get("score", {})
        overall_score = score_data.get(
            "overall", feedback_data.get("overall_score", 0.0)
        )

        def extract_score_detail(criterion: str) -> dict:
            criterion_data = feedback_data.get(criterion, {})
            return {
                "score": criterion_data.get("score", 0.0),
                "reason": criterion_data.get("reason", ""),
            }

        # Parse suggestions if present
        suggestions_data = feedback_data.get("suggestions", [])
        suggestions = []
        if suggestions_data:
            for suggestion in suggestions_data:
                if isinstance(suggestion, dict):
                    suggestions.append(
                        {
                            "original_text": suggestion.get("original_text", ""),
                            "suggested_text": suggestion.get("suggested_text", ""),
                            "category": suggestion.get("category", ""),
                            "explanation": suggestion.get("explanation", ""),
                        }
                    )

        return {
            "overall_score": overall_score,
            "task_response": extract_score_detail("task_response"),
            "coherence_cohesion": extract_score_detail("coherence_cohesion"),
            "lexical_resource": extract_score_detail("lexical_resource"),
            "grammar": extract_score_detail("grammar"),
            "summary": feedback_data.get("summary", ""),
            "ai_comment": feedback_data.get("ai_comment", ""),
            "suggestions": suggestions,
        }

    def _build_feedback_document(
        self, attempt_id: str, parsed_feedback: dict, exam: str, section: str
    ) -> dict:
        """Build feedback document for database storage"""
        feedback_id = generate_uuid()
        created_at = datetime.utcnow()
        model_version = os.getenv("OPENAI_TEXT_MODEL", "unknown")

        feedback_doc = {
            "feedback_id": feedback_id,
            "attempt_id": attempt_id,
            "feedback_type": FeedbackTypeEnum.AI.value,
            "model_version": model_version,
            "score": {
                "overall": parsed_feedback["overall_score"],
                "subscores": {
                    "task_response": parsed_feedback["task_response"],
                    "coherence_cohesion": parsed_feedback["coherence_cohesion"],
                    "lexical_resource": parsed_feedback["lexical_resource"],
                    "grammar": parsed_feedback["grammar"],
                },
            },
            "summary": parsed_feedback["summary"],
            "ai_comment": parsed_feedback["ai_comment"],
            "created_at": created_at,
        }

        # Add suggestions if present
        if parsed_feedback.get("suggestions"):
            feedback_doc["suggestions"] = parsed_feedback["suggestions"]

        return feedback_doc

    def _build_feedback_response_from_data(
        self,
        feedback_id: str,
        attempt_id: str,
        parsed_feedback: dict,
        exam: str,
        section: str,
        created_at: datetime,
    ) -> FeedbackResponse:
        """Build FeedbackResponse from parsed data"""
        model_version = os.getenv("OPENAI_TEXT_MODEL", "unknown")
        scale = get_score_scale(exam, section)

        def build_score_detail(criterion: str) -> ScoreDetail:
            return ScoreDetail(
                score=parsed_feedback[criterion]["score"],
                reason=parsed_feedback[criterion]["reason"],
            )

        # Build suggestions list if present
        suggestions = None
        if parsed_feedback.get("suggestions"):
            suggestions = [
                RevisionSuggestion(
                    original_text=s.get("original_text", ""),
                    suggested_text=s.get("suggested_text", ""),
                    category=s.get("category", ""),
                    explanation=s.get("explanation", ""),
                )
                for s in parsed_feedback["suggestions"]
            ]

        return FeedbackResponse(
            feedback_id=feedback_id,
            attempt_id=attempt_id,
            feedback_type=FeedbackTypeEnum.AI.value,
            model_version=model_version,
            score=ScoreWithSubscoresDetail(
                overall=parsed_feedback["overall_score"],
                subscores=ScoreSubscoresDetail(
                    task_response=build_score_detail("task_response"),
                    coherence_cohesion=build_score_detail("coherence_cohesion"),
                    lexical_resource=build_score_detail("lexical_resource"),
                    grammar=build_score_detail("grammar"),
                ),
                scale=scale,
            ),
            summary=parsed_feedback["summary"],
            ai_comment=parsed_feedback["ai_comment"],
            suggestions=suggestions,
            created_at=created_at,
        )

    async def generate_feedback(
        self,
        attempt_id: str,
    ) -> FeedbackResponse:
        """
        Generate AI feedback for an exam attempt
        """
        try:
            logging.info(
                f"[ExamFeedbackService] [GenerateFeedback] Starting - attempt_id={attempt_id}"
            )

            # Fetch and validate attempt
            attempt_doc = await self.attempt_repo.get_attempt_by_id(
                attempt_id=attempt_id
            )
            if not attempt_doc:
                raise ValueError(f"Attempt not found: {attempt_id}")

            # Extract attempt data
            attempt_data = self._extract_attempt_data(attempt_doc)

            # Process image extraction if needed
            input_assets = await self._process_image_extraction(
                attempt_data["input_assets"], attempt_id
            )

            # Build prompt and call LLM
            prompt = build_ielts_writing_evaluation_prompt(
                exam=attempt_data["exam"],
                section=attempt_data["section"],
                task_type=attempt_data["task_type"],
                description=attempt_data["description"],
                input_assets=input_assets,
                student_answer=attempt_data["student_answer"],
            )

            llm_response = await generate_text(prompt)
            if not llm_response or not llm_response.strip():
                raise ValueError("Empty response from LLM")

            # Parse LLM response
            feedback_data = parse_llm_json_response(
                llm_response, context="[ExamFeedbackService] [GenerateFeedback]"
            )
            parsed_feedback = self._parse_llm_feedback_response(feedback_data)

            # Build and save feedback document
            feedback_doc = self._build_feedback_document(
                attempt_id,
                parsed_feedback,
                attempt_data["exam"],
                attempt_data["section"],
            )
            await self.feedback_repo.create_feedback(feedback_doc)

            logging.info(
                f"[ExamFeedbackService] [GenerateFeedback] Success - attempt_id={attempt_id}, "
                f"score={parsed_feedback['overall_score']}, feedback_id={feedback_doc['feedback_id']}"
            )

            # Build response from data
            response = self._build_feedback_response_from_data(
                feedback_doc["feedback_id"],
                attempt_id,
                parsed_feedback,
                attempt_data["exam"],
                attempt_data["section"],
                feedback_doc["created_at"],
            )

            return response
        except ValueError:
            raise
        except Exception as e:
            logging.error(f"[ExamFeedbackService] [GenerateFeedback] Error: {str(e)}")
            logging.error(
                f"[ExamFeedbackService] [GenerateFeedback] Traceback: {traceback.format_exc()}"
            )
            raise

    async def generate_feedback_v2(
        self,
        attempt_id: str,
    ) -> dict[str, dict[str, float] | dict[Any, Any] | Any]:
        """
        Generate AI feedback for an exam attempt (new pipeline-based version).
        """
        try:
            logging.info(
                f"[ExamFeedbackService] [GenerateFeedbackV2] Starting - attempt_id={attempt_id}"
            )

            # Fetch and validate attempt
            attempt_doc = await self.attempt_repo.get_attempt_by_id(
                attempt_id=attempt_id
            )
            if not attempt_doc:
                raise ValueError(f"Attempt not found: {attempt_id}")

            # Extract attempt data
            attempt_data = self._extract_attempt_data(attempt_doc)

            student_answer_text = attempt_data.get("student_answer", {}).get("text", "")
            if not student_answer_text or not student_answer_text.strip():
                raise ValueError(
                    f"Student answer text is empty for attempt_id={attempt_id}"
                )

            logging.info(
                f"[ExamFeedbackService] [GenerateFeedbackV2] Preprocessing essay structure - attempt_id={attempt_id}, "
                f"answer_length={len(student_answer_text)}"
            )

            # Pre-process: split student's essay into sentences and paragraphs
            essay_structure = await _call_openai_json(
                build_parse_essay_structure_prompt(student_answer_text),
                log_label="preprocess_structure",
            )

            logging.info(
                f"[ExamFeedbackService] [GenerateFeedbackV2] Essay structure parsed - attempt_id={attempt_id}"
            )

            task_prompt = attempt_data.get("task_prompt", {}) or {}
            essay_prompt = task_prompt.get("essay_prompt") or task_prompt.get(
                "description", ""
            )

            # Run Task + CC + LR + GRA pipelines in parallel (depend only on essay_structure / user_input)
            (
                task_feedback,
                cc_feedback,
                lr_feedback,
                gra_feedback,
            ) = await asyncio.gather(
                run_task_feedback_pipeline(
                    attempt_data["task_type"], essay_prompt, essay_structure
                ),
                _run_criterion_pipeline(
                    essay_structure,
                    build_extracting_auditable_cc_evidence_prompt,
                    build_coherence_and_cohesion_feedback_prompt,
                    "coherence_and_cohesion",
                ),
                _run_criterion_pipeline(
                    essay_structure,
                    build_extracting_auditable_lr_evidence_prompt,
                    build_lexical_resource_feedback_prompt,
                    "lexical_resource",
                ),
                _run_criterion_pipeline(
                    essay_structure,
                    build_extracting_auditable_gra_evidence_prompt,
                    build_grammatical_range_and_accuracy_feedback_prompt,
                    "grammatical_range_and_accuracy",
                ),
            )

            task_feedback = task_feedback or {}
            cc_feedback = cc_feedback or {}
            lr_feedback = lr_feedback or {}
            gra_feedback = gra_feedback or {}

            task_score = (
                task_feedback.get("tr_band") or task_feedback.get("tc_band") or 0
            )
            cc_score = cc_feedback.get("cc_band") or 0
            lr_score = lr_feedback.get("lr_band") or 0
            gra_score = gra_feedback.get("gra_band") or 0

            total_score = overall_band(task_score, cc_score, lr_score, gra_score)

            logging.info(
                f"[ExamFeedbackService] [GenerateFeedbackV2] Scores computed - attempt_id={attempt_id}, "
                f"task={task_score}, cc={cc_score}, lr={lr_score}, gra={gra_score}, overall={total_score}"
            )

            overall_feedback = await _call_openai_json(
                build_overall_feedback_prompt(
                    essay_structure,
                    task_feedback,
                    cc_feedback,
                    lr_feedback,
                    gra_feedback,
                ),
                log_label="overall_feedback",
            )

            return {
                "score": {"overall": total_score},
                "task_response": task_feedback,
                "coherence_cohesion": cc_feedback,
                "lexical_resource": lr_feedback,
                "grammar": gra_feedback,
                "overall_feedback": overall_feedback,
            }
        except ValueError:
            raise
        except Exception as e:
            logging.error(f"[ExamFeedbackService] [GenerateFeedbackV2] Error: {str(e)}")
            logging.error(
                f"[ExamFeedbackService] [GenerateFeedbackV2] Traceback: {traceback.format_exc()}"
            )
            raise

    async def list_feedbacks(
        self, attempt_id: str, student_id: str
    ) -> FeedbackListResponse:
        """
        List all feedbacks for a specific attempt
        """
        try:
            logging.info(
                f"""[ExamFeedbackService] [ListFeedbacks] Starting - attempt_id={attempt_id}, student_id={student_id}"""
            )

            # Verify attempt exists
            attempt_doc = await self.attempt_repo.get_attempt_by_id(
                attempt_id=attempt_id
            )
            if not attempt_doc:
                logging.warning(
                    f"""[ExamFeedbackService] [ListFeedbacks] Attempt not found: {attempt_id}"""
                )
                raise HTTPException(
                    status_code=404, detail=f"Attempt not found: {attempt_id}"
                )

            # Authorization check: users can only access feedbacks for their own attempts
            attempt_student_id = attempt_doc.get("student_id")
            if attempt_student_id != student_id:
                logging.warning(
                    f"""[ExamFeedbackService] [ListFeedbacks] Unauthorized access attempt - attempt_id={attempt_id}, student_id={student_id}, attempt_student_id={attempt_student_id}"""
                )
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to access feedbacks for this attempt",
                )

            # Get feedbacks from repository
            feedbacks_data, total = await self.feedback_repo.list_feedbacks(
                attempt_id=attempt_id
            )

            feedback_items = []
            for feedback_doc in feedbacks_data:
                try:
                    created_at_value = feedback_doc.get("created_at")
                    feedback_items.append(
                        await self._build_feedback_response(
                            feedback_doc, attempt_id, attempt_doc, created_at_value
                        )
                    )
                except Exception as e:
                    logging.warning(
                        f"""[ExamFeedbackService] [ListFeedbacks] Skipping invalid feedback document: {str(e)}"""
                    )

            logging.info(
                f"""[ExamFeedbackService] [ListFeedbacks] Successfully retrieved {len(feedback_items)}/{total} feedbacks (attempt_id={attempt_id})"""
            )

            return FeedbackListResponse(items=feedback_items, total=total)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"""[ExamFeedbackService] [ListFeedbacks] Error retrieving feedbacks - attempt_id={attempt_id}, error: {str(e)}"""
            )
            logging.error(
                f"""[ExamFeedbackService] [ListFeedbacks] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def generate_model_essay(
        self, attempt_id: str, feedback_id: str, student_id: str
    ) -> Optional[ModelEssayInfo]:
        """
        Get model essay associated with a feedback and attempt.
        This is a separate API endpoint - model essays are only generated when user clicks "Generate Model Essay".

        Authorization:
        - Users can only access model essays for their own attempts
        """
        try:
            # Verify attempt exists and belongs to student
            attempt_doc = await self.attempt_repo.get_attempt_by_id(
                attempt_id=attempt_id
            )
            if not attempt_doc:
                raise ValueError(f"Attempt not found: {attempt_id}")

            attempt_student_id = attempt_doc.get("student_id")
            if attempt_student_id != student_id:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to access model essays for this attempt",
                )

            # Check if model essay already exists
            model_essay_doc = await self.feedback_repo.get_model_essay_by_attempt(
                attempt_id=attempt_id,
            )

            if model_essay_doc:
                # Return existing model essay
                logging.info(
                    f"[ExamFeedbackService] [GetModelEssay] Found existing model essay - attempt_id={attempt_id}, feedback_id={feedback_id}, model_essay_id={model_essay_doc.get('model_essay_id')}"
                )
                return ModelEssayInfo(
                    model_essay_id=model_essay_doc.get("model_essay_id", ""),
                    target_score=model_essay_doc.get("target_score", 8.0),
                    essay_content=model_essay_doc.get("content", ""),
                    model_version=model_essay_doc.get("model_version"),
                    analysis=model_essay_doc.get("analysis", ""),
                    band_score=model_essay_doc.get("band_score", 0.0),
                    created_at=model_essay_doc.get("created_at"),
                )

            # Generate new model essay
            logging.info(
                f"[ExamFeedbackService] [GetModelEssay] Generating new model essay - attempt_id={attempt_id}, feedback_id={feedback_id}"
            )

            # Prepare attempt data for prompt
            task_prompt = attempt_doc.get("task_prompt", {})
            description = task_prompt.get("description", "")
            student_answer = attempt_doc.get("student_answer", {})
            student_answer_text = (
                student_answer.get("text", "") if student_answer else ""
            )

            # Validate that student answer exists (required for improving the essay)
            if not student_answer_text or not student_answer_text.strip():
                raise ValueError(
                    "Student answer is required to generate a model essay. Please provide the student's answer first."
                )

            attempt_data = {
                "description": description,
                "student_answer": student_answer_text,
            }

            # Include image_text if available (stored in input_assets)
            input_assets = task_prompt.get("input_assets", {})
            if input_assets and input_assets.get("image_text"):
                attempt_data["image_text"] = input_assets["image_text"]

            # Build prompt and call LLM
            prompt = build_model_essay_prompt(attempt_data)
            # Use lower temperature for more consistent, high-quality output
            # Increase max_tokens to ensure complete essay generation
            llm_response = await generate_text(prompt, temperature=0.3, max_tokens=4000)

            if not llm_response or not llm_response.strip():
                raise ValueError("Empty response from LLM when generating model essay")

            # Parse LLM response
            model_essay_data = parse_llm_json_response(
                llm_response, context="[ExamFeedbackService] [GetModelEssay]"
            )

            # Extract model essay information
            target_score = model_essay_data.get("target_score", 8.0)
            content = model_essay_data.get("content", "")
            analysis = model_essay_data.get("analysis", "Analysis not available.")

            if not content:
                raise ValueError("Model essay content is empty")

            # Generate model essay ID and prepare document
            model_essay_id = generate_uuid()
            model_version = os.getenv("OPENAI_TEXT_MODEL", "unknown")
            created_at = datetime.utcnow()

            model_essay_doc = {
                "model_essay_id": model_essay_id,
                "attempt_id": attempt_id,
                "feedback_id": feedback_id,
                "target_score": target_score,
                "content": content,
                "analysis": analysis,
                "model_version": model_version,
                "created_at": created_at,
            }

            # Save to database
            inserted_doc = await self.feedback_repo.create_model_essay(model_essay_doc)

            if not inserted_doc:
                raise ValueError(
                    f"Failed to save model essay to database: {model_essay_id}"
                )

            logging.info(
                f"[ExamFeedbackService] [GetModelEssay] Successfully generated and saved model essay - attempt_id={attempt_id}, feedback_id={feedback_id}, model_essay_id={model_essay_id}"
            )

            return ModelEssayInfo(
                model_essay_id=model_essay_id,
                band_score=target_score,
                essay_content=content,
                analysis=analysis,
                model_version=model_version,
                created_at=created_at,
            )
        except HTTPException:
            raise
        except ValueError:
            raise
        except Exception as e:
            logging.error(
                f"[ExamFeedbackService] [GetModelEssay] Error retrieving model essay - attempt_id={attempt_id}, feedback_id={feedback_id}: {str(e)}"
            )
            logging.error(
                f"[ExamFeedbackService] [GetModelEssay] Traceback: {traceback.format_exc()}"
            )
            raise

    async def get_model_essay_by_attempt(
        self, attempt_id: str, student_id: str
    ) -> Optional[ModelEssayInfo]:
        """
        Get model essay associated with an attempt.
        This endpoint retrieves an existing model essay without generating a new one.

        Authorization:
        - Users can only access model essays for their own attempts
        """
        try:
            # Verify attempt exists and belongs to student
            attempt_doc = await self.attempt_repo.get_attempt_by_id(
                attempt_id=attempt_id
            )
            if not attempt_doc:
                raise ValueError(f"Attempt not found: {attempt_id}")

            attempt_student_id = attempt_doc.get("student_id")
            if attempt_student_id != student_id:
                raise HTTPException(
                    status_code=403,
                    detail="You do not have permission to access model essays for this attempt",
                )

            # Get model essay from repository
            model_essay_doc = await self.feedback_repo.get_model_essay_by_attempt(
                attempt_id=attempt_id,
            )

            if not model_essay_doc:
                logging.info(
                    f"[ExamFeedbackService] [GetModelEssayByAttempt] Model essay not found - attempt_id={attempt_id}"
                )
                return None

            # Convert dict to ModelEssayInfo
            logging.info(
                f"[ExamFeedbackService] [GetModelEssayByAttempt] Found model essay - attempt_id={attempt_id}, model_essay_id={model_essay_doc.get('model_essay_id')}"
            )
            return ModelEssayInfo(
                model_essay_id=model_essay_doc.get("model_essay_id", ""),
                band_score=model_essay_doc.get("target_score", 8.0),
                essay_content=model_essay_doc.get("content", ""),
                analysis=model_essay_doc.get("analysis", "Analysis not available."),
                model_version=model_essay_doc.get("model_version"),
                created_at=model_essay_doc.get("created_at", datetime.utcnow()),
            )
        except HTTPException:
            raise
        except ValueError:
            raise
        except Exception as e:
            logging.error(
                f"[ExamFeedbackService] [GetModelEssayByAttempt] Error retrieving model essay - attempt_id={attempt_id}"
            )
            logging.error(
                f"[ExamFeedbackService] [GetModelEssayByAttempt] Traceback: {traceback.format_exc()}"
            )
            raise
