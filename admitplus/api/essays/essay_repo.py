import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class EssayRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.essay_repo = BaseMongoCRUD(self.db_name)

        self.essay_collection = settings.ESSAY_COLLECTION
        self.essay_drafts_collection = settings.ESSAY_DRAFTS_COLLECTION
        self.essay_records_collection = settings.ESSAY_RECORDS_COLLECTION
        self.essay_conversations_collection = settings.ESSAY_CONVERSATIONS_COLLECTION
        self.essay_questions_collection = settings.ESSAY_QUESTIONS_COLLECTION

    # ============================================================================
    # Essay CRUD Operations
    # ============================================================================

    async def create_essay(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new essay document in the database
        """
        try:
            inserted_id = await self.essay_repo.insert_one(
                document=data, collection_name=self.essay_collection
            )
            logging.info(
                f"""[EssayRepo] [CreateEssay] Successfully created essay (inserted_id: {inserted_id})"""
            )
            logging.info(
                f"""[EssayRepo] [CreateEssay] Data inserted into DB: {self.db_name}, Collection: {self.essay_collection}"""
            )
            return inserted_id
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [CreateEssay] Error creating essay: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [CreateEssay] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def find_many_application_essays(self, application_id):
        """
        Find all essays for a given application_id
        """
        try:
            essay_list = await self.essay_repo.find_many(
                query={"application_id": application_id},
                collection_name=self.essay_collection,
            )
            logging.info(
                f"""[EssayRepo] [FindApplicationEssays] Successfully found {len(essay_list)} essay(s) for application_id={application_id}"""
            )
            logging.info(
                f"""[EssayRepo] [FindApplicationEssays] Query executed on DB: {self.db_name}, Collection: {self.essay_collection}"""
            )
            return essay_list
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [FindApplicationEssays] Error finding essays for application_id={application_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [FindApplicationEssays] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_essay_by_id(self, essay_id):
        """
        Find essay by essay_id
        """
        try:
            essay_detail = await self.essay_repo.find_one(
                query={"essay_id": essay_id}, collection_name=self.essay_collection
            )
            if essay_detail:
                logging.info(
                    f"""[EssayRepo] [GetEssayById] Successfully found essay for essay_id={essay_id}"""
                )
            else:
                logging.warning(
                    f"""[EssayRepo] [GetEssayById] Essay not found for essay_id={essay_id}"""
                )
            logging.info(
                f"""[EssayRepo] [GetEssayById] Query executed on DB: {self.db_name}, Collection: {self.essay_collection}"""
            )
            return essay_detail
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [GetEssayById] Error finding essay for essay_id={essay_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [GetEssayById] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def update_essay(self, essay_id: str, update_data: Dict[str, Any]) -> int:
        """
        Update essay by essay_id
        """
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()

            modified_count = await self.essay_repo.update_one(
                query={"essay_id": essay_id},
                update={"$set": update_data},
                collection_name=self.essay_collection,
            )
            logging.info(
                f"""[EssayRepo] [UpdateEssay] Successfully updated {modified_count} essay(s) for essay_id={essay_id}"""
            )
            logging.info(
                f"""[EssayRepo] [UpdateEssay] Query executed on DB: {self.db_name}, Collection: {self.essay_collection}"""
            )
            return modified_count
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [UpdateEssay] Error updating essay for essay_id={essay_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [UpdateEssay] Traceback: {traceback.format_exc()}"""
            )
            raise

    # ============================================================================
    # Essay Draft Operations
    # ============================================================================

    async def list_essay_drafts(
        self, essay_id: str, page: int = 1, page_size: int = 10
    ):
        """
        Find all essay drafts for a given essay_id with pagination
        """
        try:
            drafts, total = await self.essay_repo.find_many_paginated(
                query={"essay_id": essay_id},
                page=page,
                page_size=page_size,
                sort={"created_at": -1},  # Sort by created_at descending (newest first)
                collection_name=self.essay_drafts_collection,
            )
            logging.info(
                f"""[EssayRepo] [ListEssayDrafts] Successfully found {len(drafts)} draft(s) for essay_id={essay_id}"""
            )
            logging.info(
                f"""[EssayRepo] [ListEssayDrafts] Query executed on DB: {self.db_name}, Collection: {self.essay_drafts_collection}"""
            )
            return drafts, total
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [ListEssayDrafts] Error finding drafts for essay_id={essay_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [ListEssayDrafts] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def insert_essay_draft(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new essay draft document in the database
        """
        try:
            inserted_id = await self.essay_repo.insert_one(
                document=data, collection_name=self.essay_drafts_collection
            )
            logging.info(
                f"""[EssayRepo] [InsertEssayDraft] Successfully created draft (inserted_id: {inserted_id})"""
            )
            logging.info(
                f"""[EssayRepo] [InsertEssayDraft] Data inserted into DB: {self.db_name}, Collection: {self.essay_drafts_collection}"""
            )
            return inserted_id
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [InsertEssayDraft] Error creating draft: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [InsertEssayDraft] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_draft_by_id(self, draft_id: str):
        """
        Find essay draft by draft_id
        """
        try:
            draft_detail = await self.essay_repo.find_one(
                query={"draft_id": draft_id},
                collection_name=self.essay_drafts_collection,
            )
            if draft_detail:
                logging.info(
                    f"""[EssayRepo] [GetDraftById] Successfully found draft for draft_id={draft_id}"""
                )
            else:
                logging.warning(
                    f"""[EssayRepo] [GetDraftById] Draft not found for draft_id={draft_id}"""
                )
            logging.info(
                f"""[EssayRepo] [GetDraftById] Query executed on DB: {self.db_name}, Collection: {self.essay_drafts_collection}"""
            )
            return draft_detail
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [GetDraftById] Error finding draft for draft_id={draft_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [GetDraftById] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_max_version_for_essay(self, essay_id: str) -> int:
        """
        Get the maximum version number for a given essay_id
        Returns 0 if no drafts exist for this essay_id
        Version auto-increments for each new draft of the same essay_id
        """
        try:
            # Find drafts sorted by version descending, only project version field for efficiency
            # Get the first draft (highest version) to determine next version
            drafts = await self.essay_repo.find_many(
                query={"essay_id": essay_id},
                projection={"version": 1},  # Only fetch version field for efficiency
                sort={"version": -1},  # Sort descending to get max version first
                collection_name=self.essay_drafts_collection,
            )

            if drafts:
                # Get the first draft (highest version) and return its version
                max_version = drafts[0].get("version", 0)
                logging.info(
                    f"""[EssayRepo] [GetMaxVersionForEssay] Found max version {max_version} for essay_id={essay_id}"""
                )
                return max_version
            else:
                logging.info(
                    f"""[EssayRepo] [GetMaxVersionForEssay] No drafts found for essay_id={essay_id}, returning 0"""
                )
                return 0
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [GetMaxVersionForEssay] Error getting max version for essay_id={essay_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [GetMaxVersionForEssay] Traceback: {traceback.format_exc()}"""
            )
            raise

    # ============================================================================
    # Essay Record Operations
    # ============================================================================

    async def insert_essay_record(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new essay record document in the database
        Essay records store request/response for essay generation operations
        """
        try:
            inserted_id = await self.essay_repo.insert_one(
                document=data, collection_name=self.essay_records_collection
            )
            logging.info(
                f"""[EssayRepo] [InsertEssayRecord] Successfully created record (inserted_id: {inserted_id})"""
            )
            logging.info(
                f"""[EssayRepo] [InsertEssayRecord] Data inserted into DB: {self.db_name}, Collection: {self.essay_records_collection}"""
            )
            return inserted_id
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [InsertEssayRecord] Error creating record: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [InsertEssayRecord] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def find_many_essay_records(self, essay_id: str):
        """
        Find all essay records for a given essay_id
        """
        try:
            records = await self.essay_repo.find_many(
                query={"essay_id": essay_id},
                sort={"created_at": -1},  # Sort by created_at descending (newest first)
                collection_name=self.essay_records_collection,
            )
            logging.info(
                f"""[EssayRepo] [FindManyEssayRecords] Successfully found {len(records)} record(s) for essay_id={essay_id}"""
            )
            logging.info(
                f"""[EssayRepo] [FindManyEssayRecords] Query executed on DB: {self.db_name}, Collection: {self.essay_records_collection}"""
            )
            return records
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [FindManyEssayRecords] Error finding records for essay_id={essay_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [FindManyEssayRecords] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_essay_record_by_id(self, record_id: str):
        """
        Find essay record by record_id
        """
        try:
            record_detail = await self.essay_repo.find_one(
                query={"record_id": record_id},
                collection_name=self.essay_records_collection,
            )
            if record_detail:
                logging.info(
                    f"""[EssayRepo] [GetEssayRecordById] Successfully found record for record_id={record_id}"""
                )
            else:
                logging.warning(
                    f"""[EssayRepo] [GetEssayRecordById] Record not found for record_id={record_id}"""
                )
            logging.info(
                f"""[EssayRepo] [GetEssayRecordById] Query executed on DB: {self.db_name}, Collection: {self.essay_records_collection}"""
            )
            return record_detail
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [GetEssayRecordById] Error finding record for record_id={record_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [GetEssayRecordById] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def create_essay_question(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new essay question document in the database
        """
        try:
            inserted_id = await self.essay_repo.insert_one(
                document=data, collection_name=self.essay_questions_collection
            )
            logging.info(
                f"""[EssayRepo] [CreateEssayQuestion] Successfully created essay question (inserted_id: {inserted_id})"""
            )
            logging.info(
                f"""[EssayRepo] [CreateEssayQuestion] Data inserted into DB: {self.db_name}, Collection: {self.essay_questions_collection}"""
            )
            return inserted_id
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [CreateEssayQuestion] Error creating essay question: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [CreateEssayQuestion] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def update_essay_question(
        self, question_id: str, update_data: Dict[str, Any]
    ) -> int:
        """
        Update essay question by question_id
        """
        try:
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()

            modified_count = await self.essay_repo.update_one(
                query={"question_id": question_id},
                update={"$set": update_data},
                collection_name=self.essay_questions_collection,
            )
            logging.info(
                f"""[EssayRepo] [UpdateEssayQuestion] Successfully updated {modified_count} question(s) for question_id={question_id}"""
            )
            logging.info(
                f"""[EssayRepo] [UpdateEssayQuestion] Query executed on DB: {self.db_name}, Collection: {self.essay_questions_collection}"""
            )
            return modified_count
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [UpdateEssayQuestion] Error updating question for question_id={question_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [UpdateEssayQuestion] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_essay_question_by_essay_id(self, essay_id: str):
        """
        Find all essay questions for a given essay_id
        """
        try:
            questions = await self.essay_repo.find_many(
                query={"essay_id": essay_id},
                sort={"created_at": 1},  # Sort by created_at ascending (oldest first)
                collection_name=self.essay_questions_collection,
            )
            logging.info(
                f"""[EssayRepo] [GetEssayQuestionByEssayId] Successfully found {len(questions)} question(s) for essay_id={essay_id}"""
            )
            logging.info(
                f"""[EssayRepo] [GetEssayQuestionByEssayId] Query executed on DB: {self.db_name}, Collection: {self.essay_questions_collection}"""
            )
            return questions
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [GetEssayQuestionByEssayId] Error finding questions for essay_id={essay_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [GetEssayQuestionByEssayId] Traceback: {traceback.format_exc()}"""
            )
            raise

    async def get_essay_question_by_id(self, question_id: str):
        """
        Find essay question by question_id
        """
        try:
            question_detail = await self.essay_repo.find_one(
                query={"question_id": question_id},
                collection_name=self.essay_questions_collection,
            )
            if question_detail:
                logging.info(
                    f"""[EssayRepo] [GetEssayQuestionById] Successfully found question for question_id={question_id}"""
                )
            else:
                logging.warning(
                    f"""[EssayRepo] [GetEssayQuestionById] Question not found for question_id={question_id}"""
                )
            logging.info(
                f"""[EssayRepo] [GetEssayQuestionById] Query executed on DB: {self.db_name}, Collection: {self.essay_questions_collection}"""
            )
            return question_detail
        except Exception as e:
            logging.error(
                f"""[EssayRepo] [GetEssayQuestionById] Error finding question for question_id={question_id}: {str(e)}"""
            )
            logging.error(
                f"""[EssayRepo] [GetEssayQuestionById] Traceback: {traceback.format_exc()}"""
            )
            raise
