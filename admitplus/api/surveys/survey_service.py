import logging
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any

from .survey_repo import SurveyRepo
from .survey_schema import (
    ShouldShowQuestionsResponse,
    Survey,
    Question,
    QuestionOption,
    SurveySubmissionResponse,
    ErrorDetail,
)


class SurveyService:
    def __init__(self):
        self.survey_repo = SurveyRepo()

    def _build_error_response(
        self, code: str, message: str
    ) -> SurveySubmissionResponse:
        """Helper method to build error response."""
        return SurveySubmissionResponse(
            success=False, error=ErrorDetail(code=code, message=message)
        )

    def _convert_questions(self, questions_data: List[Dict]) -> List[Question]:
        """Convert database questions to response model."""
        return [
            Question(
                id=q.get("id", ""),
                type=q.get("type", ""),
                text=q.get("text", ""),
                options=[
                    QuestionOption(
                        value=opt.get("value", ""), label=opt.get("label", "")
                    )
                    for opt in q.get("options", [])
                ],
            )
            for q in questions_data
        ]

    async def should_show_questions(
        self, feature_key: str, user_id: str
    ) -> ShouldShowQuestionsResponse:
        """
        Check if survey questions should be shown for a given feature key.

        Conditions checked:
        1. Is there an active survey for the current feature?
        2. Has the user answered this survey (same feature_key and version)?
        """
        try:
            survey_doc = await self.survey_repo.find_survey_questions(feature_key)
            if not survey_doc:
                return ShouldShowQuestionsResponse(show=False)

            survey_version = survey_doc.get("version", 1)
            existing_answer = (
                await self.survey_repo.find_survey_answer_by_user_and_survey(
                    user_id=user_id, feature_key=feature_key, version=survey_version
                )
            )

            if existing_answer:
                return ShouldShowQuestionsResponse(show=False)

            survey = Survey(
                featureKey=survey_doc.get("feature_key", feature_key),
                version=survey_version,
                questions=self._convert_questions(survey_doc.get("questions", [])),
            )

            return ShouldShowQuestionsResponse(show=True, survey=survey)

        except Exception as e:
            logging.error(f"[SurveyService] [ShouldShowQuestions] Error: {str(e)}")
            logging.error(traceback.format_exc())
            return ShouldShowQuestionsResponse(show=False)

    async def submit_survey_answers(
        self, question_data: Dict[str, Any], user_id: str
    ) -> SurveySubmissionResponse:
        """
        Submit survey answers or dismiss survey.

        Validates:
        1. If status is "completed", answers must be provided
        2. Submitted version must match active survey version
        3. User hasn't already answered this survey
        """
        try:
            feature_key = question_data.get("featureKey")
            survey_version = question_data.get("surveyVersion")
            status = question_data.get("status")
            answers = question_data.get("answers")

            # Validate answers for completed status
            if status == "completed" and not answers:
                return self._build_error_response(
                    "MISSING_ANSWERS",
                    "Answers are required when status is 'completed'.",
                )

            # Check active survey
            survey_doc = await self.survey_repo.find_survey_questions(feature_key)
            if not survey_doc:
                return self._build_error_response(
                    "SURVEY_NOT_FOUND", "No active survey found for this feature."
                )

            # Validate version
            active_version = survey_doc.get("version", 1)
            if survey_version != active_version:
                logging.warning(
                    f"[SurveyService] [SubmitSurveyAnswers] Version mismatch: {survey_version} != {active_version}"
                )
                return self._build_error_response(
                    "INVALID_SURVEY_VERSION",
                    "Submitted version does not match active survey version.",
                )

            # Check duplicate answer
            existing_answer = (
                await self.survey_repo.find_survey_answer_by_user_and_survey(
                    user_id=user_id, feature_key=feature_key, version=survey_version
                )
            )
            if existing_answer:
                return self._build_error_response(
                    "ALREADY_ANSWERED", "You have already answered this survey."
                )

            # Save survey answer
            survey_answer_doc = {
                "user_id": user_id,
                "survey_question_id": question_data.get("survey_question_id"),
                "feature_key": feature_key,
                "version": survey_version,
                "status": status,
                "answers": answers if status == "completed" else None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            insert_id = await self.survey_repo.create_survey_answer(survey_answer_doc)
            if not insert_id:
                logging.error(
                    f"[SurveyService] [SubmitSurveyAnswers] Failed to save answer for user {user_id}"
                )
                return self._build_error_response(
                    "DATABASE_ERROR", "Failed to save survey answer."
                )

            return SurveySubmissionResponse(success=True)

        except Exception as e:
            logging.error(f"[SurveyService] [SubmitSurveyAnswers] Error: {str(e)}")
            logging.error(traceback.format_exc())
            return self._build_error_response(
                "INTERNAL_ERROR",
                "An internal error occurred while processing your request.",
            )
