import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class SurveyRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.survey_questions_collection = settings.SURVEY_QUESTIONS_COLLECTION
        self.survey_answers_collection = settings.SURVEY_ANSWERS_COLLECTION

        logging.info(f"[SurveyRepo] Initialized with db: {self.db_name}")
        logging.info(
            f"[SurveyRepo] Collections - Questions: {self.survey_questions_collection}, Answers: {self.survey_answers_collection}"
        )

    async def find_survey_questions(self, feature_key: str) -> Optional[Dict[str, Any]]:
        """
        Find survey questions for a given feature_key.
        Returns the document with the largest version for the given feature_key, or None if not found.
        """
        try:
            logging.info(
                f"[SurveyRepo] [FindSurveyQuestions] Starting search for feature_key: {feature_key}"
            )

            query_filter = {"feature_key": feature_key, "isActive": True}

            # Find the document with the largest version for the given feature_key
            result = await self.mongo_repo.find_many(
                query=query_filter,
                sort={
                    "version": -1
                },  # Sort by version descending to get the largest version
                collection_name=self.survey_questions_collection,
            )

            # Return the first result (largest version), or None if not found
            survey_doc = result[0] if result else None

            if survey_doc:
                version = survey_doc.get("version", "unknown")
                logging.info(
                    f"[SurveyRepo] [FindSurveyQuestions] Found survey questions for feature_key: {feature_key}, version: {version}"
                )
            else:
                logging.warning(
                    f"[SurveyRepo] [FindSurveyQuestions] No active survey questions found for feature_key: {feature_key}"
                )

            return survey_doc

        except Exception as e:
            logging.error(
                f"[SurveyRepo] [FindSurveyQuestions] Error finding survey questions for feature_key {feature_key}: {str(e)}"
            )
            logging.error(
                f"[SurveyRepo] [FindSurveyQuestions] Traceback: {traceback.format_exc()}"
            )
            raise

    async def create_survey_question(
        self, survey_question: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a new survey question document in the database.
        Returns the inserted document ID.
        """
        try:
            feature_key = survey_question.get("feature_key", "unknown")
            version = survey_question.get("version", "unknown")

            logging.info(
                f"[SurveyRepo] [CreateSurveyQuestion] Starting survey question creation"
            )
            logging.info(
                f"[SurveyRepo] [CreateSurveyQuestion] Feature key: {feature_key}, Version: {version}"
            )

            insert_id = await self.mongo_repo.insert_one(
                document=survey_question,
                collection_name=self.survey_questions_collection,
            )

            if insert_id:
                logging.info(
                    f"[SurveyRepo] [CreateSurveyQuestion] Successfully created survey question (inserted_id: {insert_id})"
                )
                logging.info(
                    f"[SurveyRepo] [CreateSurveyQuestion] Data inserted into DB: {self.db_name}, Collection: {self.survey_questions_collection}"
                )
            else:
                logging.error(
                    f"[SurveyRepo] [CreateSurveyQuestion] Failed to create survey question - insert_id is None"
                )
            return insert_id
        except Exception as e:
            logging.error(
                f"[SurveyRepo] [CreateSurveyQuestion] Error creating survey question: {str(e)}"
            )
            logging.error(
                f"[SurveyRepo] [CreateSurveyQuestion] Survey question data: {survey_question}"
            )
            logging.error(
                f"[SurveyRepo] [CreateSurveyQuestion] Traceback: {traceback.format_exc()}"
            )
            raise

    async def create_survey_answer(
        self, survey_answer: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a new survey answer document in the database.
        Returns the inserted document ID.
        """
        try:
            user_id = survey_answer.get("user_id")

            logging.info(
                f"[SurveyRepo] [CreateSurveyAnswer] Starting survey answer creation"
            )

            insert_id = await self.mongo_repo.insert_one(
                document=survey_answer, collection_name=self.survey_answers_collection
            )

            if insert_id:
                logging.info(
                    f"[SurveyRepo] [CreateSurveyAnswer] Successfully created survey answer (inserted_id: {insert_id})"
                )
                logging.info(
                    f"[SurveyRepo] [CreateSurveyAnswer] Data inserted into DB: {self.db_name}, Collection: {self.survey_answers_collection}"
                )
            else:
                logging.error(
                    f"[SurveyRepo] [CreateSurveyAnswer] Failed to create survey answer - insert_id is None"
                )
            return insert_id

        except Exception as e:
            logging.error(
                f"[SurveyRepo] [CreateSurveyAnswer] Error creating survey answer: {str(e)}"
            )
            logging.error(
                f"[SurveyRepo] [CreateSurveyAnswer] Survey answer data: {survey_answer}"
            )
            logging.error(
                f"[SurveyRepo] [CreateSurveyAnswer] Traceback: {traceback.format_exc()}"
            )
            raise

    async def find_survey_answer_by_user_and_survey(
        self, user_id: str, feature_key: str, version: int
    ) -> Optional[Dict[str, Any]]:
        """
        Find if user has answered a specific survey (feature_key + version).
        Returns the survey answer document if found, None otherwise.
        """
        try:
            logging.info(
                f"[SurveyRepo] [FindSurveyAnswerByUserAndSurvey] Checking - user_id: {user_id}, feature_key: {feature_key}, version: {version}"
            )

            query_filter = {
                "user_id": user_id,
                "feature_key": feature_key,
                "version": version,
            }

            result = await self.mongo_repo.find_one(
                query=query_filter, collection_name=self.survey_answers_collection
            )

            if result:
                logging.info(
                    f"[SurveyRepo] [FindSurveyAnswerByUserAndSurvey] Found survey answer for user_id: {user_id}, feature_key: {feature_key}, version: {version}"
                )
            else:
                logging.info(
                    f"[SurveyRepo] [FindSurveyAnswerByUserAndSurvey] No survey answer found for user_id: {user_id}, feature_key: {feature_key}, version: {version}"
                )

            return result

        except Exception as e:
            logging.error(
                f"[SurveyRepo] [FindSurveyAnswerByUserAndSurvey] Error finding survey answer: {str(e)}"
            )
            logging.error(
                f"[SurveyRepo] [FindSurveyAnswerByUserAndSurvey] Traceback: {traceback.format_exc()}"
            )
            raise
