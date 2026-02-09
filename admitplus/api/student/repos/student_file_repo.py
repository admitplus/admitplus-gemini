import logging
from typing import Dict, Any, Optional, List, Tuple

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class StudentFileRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.file_metadata_collection = settings.FILE_METADATA_COLLECTION
        self.files_storage_collection = settings.FILES_STORAGE_COLLECTION
        self.application_documents_collection = (
            settings.APPLICATION_DOCUMENTS_COLLECTION
        )

    async def find_file_storage_by_id(
        self,
        file_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find file from files_storage collection by file_id
        """
        try:
            logging.info(
                f"[Student File Repo] [Find File Storage] Finding file {file_id} in files_storage"
            )
            result = await self.mongo_repo.find_one(
                query={"file_id": file_id, "deleted": {"$ne": True}},
                collection_name=self.files_storage_collection,
            )
            if result:
                logging.info(
                    f"[Student File Repo] [Find File Storage] Found file {file_id} in files_storage"
                )
            else:
                logging.warning(
                    f"[Student File Repo] [Find File Storage] File {file_id} not found in files_storage"
                )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Find File Storage] Error finding file: {str(e)}"
            )
            raise

    async def find_file_metadata_by_id(
        self,
        file_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find file metadata from file_metadata collection by file_id
        """
        try:
            logging.info(
                f"[Student File Repo] [Find File Metadata] Finding file {file_id} in file_metadata"
            )
            result = await self.mongo_repo.find_one(
                query={"file_id": file_id, "deleted": {"$ne": True}},
                collection_name=self.file_metadata_collection,
            )
            if result:
                logging.info(
                    f"[Student File Repo] [Find File Metadata] Found file {file_id} in file_metadata"
                )
            else:
                logging.warning(
                    f"[Student File Repo] [Find File Metadata] File {file_id} not found in file_metadata"
                )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Find File Metadata] Error finding file: {str(e)}"
            )
            raise

    async def find_file_metadata_by_student_and_file(
        self,
        student_id: str,
        file_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find file metadata by student_id and file_id
        """
        try:
            logging.info(
                f"[Student File Repo] [Find File Metadata] Finding file {file_id} for student {student_id}"
            )
            result = await self.mongo_repo.find_one(
                query={
                    "file_id": file_id,
                    "student_id": student_id,
                    "deleted": {"$ne": True},
                },
                collection_name=self.file_metadata_collection,
            )
            if result:
                logging.info(
                    f"[Student File Repo] [Find File Metadata] Found file {file_id} for student {student_id}"
                )
            else:
                logging.warning(
                    f"[Student File Repo] [Find File Metadata] File {file_id} not found for student {student_id}"
                )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Find File Metadata] Error finding file: {str(e)}"
            )
            raise

    async def insert_file_metadata(
        self,
        document: Dict[str, Any],
    ) -> Optional[str]:
        """
        Insert a new file metadata document
        """
        try:
            logging.info(
                f"[Student File Repo] [Insert File Metadata] Inserting file metadata"
            )
            result = await self.mongo_repo.insert_one(
                document=document, collection_name=self.file_metadata_collection
            )
            if result:
                logging.info(
                    f"[Student File Repo] [Insert File Metadata] Successfully inserted file metadata"
                )
            else:
                logging.error(
                    f"[Student File Repo] [Insert File Metadata] Failed to insert file metadata"
                )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Insert File Metadata] Error inserting file metadata: {str(e)}"
            )
            raise

    async def find_student_files_paginated(
        self,
        student_id: str,
        page: int,
        page_size: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Find all files for a student with pagination
        Returns tuple of (files list, total count)
        """
        try:
            logging.info(
                f"[Student File Repo] [Find Student Files] Finding files for student {student_id}, page {page}, page_size {page_size}"
            )
            query_filter = {"student_id": student_id, "deleted": {"$ne": True}}
            sort = {"created_at": -1}
            files, total = await self.mongo_repo.find_many_paginated(
                query=query_filter,
                page=page,
                page_size=page_size,
                sort=sort,
                collection_name=self.file_metadata_collection,
            )
            logging.info(
                f"[Student File Repo] [Find Student Files] Found {len(files)} files out of {total} total"
            )
            return files, total
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Find Student Files] Error finding files: {str(e)}"
            )
            raise

    async def delete_file_metadata(self, file_id: str) -> int:
        """
        Delete file metadata by file_id
        Returns number of deleted documents
        """
        try:
            logging.info(
                f"[Student File Repo] [Delete File Metadata] Deleting file {file_id} from file_metadata"
            )
            result = await self.mongo_repo.delete_one(
                query={"file_id": file_id},
                collection_name=self.file_metadata_collection,
            )
            logging.info(
                f"[Student File Repo] [Delete File Metadata] Deleted {result} document(s) from file_metadata"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Delete File Metadata] Error deleting file: {str(e)}"
            )
            raise

    async def delete_file_storage(self, file_id: str) -> int:
        """
        Delete file from files_storage collection by file_id
        Returns number of deleted documents
        """
        try:
            logging.info(
                f"[Student File Repo] [Delete File Storage] Deleting file {file_id} from files_storage"
            )
            result = await self.mongo_repo.delete_one(
                query={"file_id": file_id},
                collection_name=self.files_storage_collection,
            )
            logging.info(
                f"[Student File Repo] [Delete File Storage] Deleted {result} document(s) from files_storage"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Delete File Storage] Error deleting file: {str(e)}"
            )
            raise

    async def find_application_documents_by_file_id(
        self,
        file_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Find application documents by file_id
        """
        try:
            logging.info(
                f"[Student File Repo] [Find Application Documents] Finding application documents for file {file_id}"
            )
            result = await self.mongo_repo.find_many(
                query={"file_id": file_id},
                collection_name=self.application_documents_collection,
            )
            logging.info(
                f"[Student File Repo] [Find Application Documents] Found {len(result)} application document(s) for file {file_id}"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Find Application Documents] Error finding application documents: {str(e)}"
            )
            raise

    async def delete_application_documents_by_file_id(
        self,
        file_id: str,
    ) -> int:
        """
        Delete application documents by file_id
        Returns number of deleted documents
        """
        try:
            logging.info(
                f"[Student File Repo] [Delete Application Documents] Deleting application documents for file {file_id}"
            )
            result = await self.mongo_repo.delete_many(
                query={"file_id": file_id},
                collection_name=self.application_documents_collection,
            )
            logging.info(
                f"[Student File Repo] [Delete Application Documents] Deleted {result} application document(s) for file {file_id}"
            )
            return result
        except Exception as e:
            logging.error(
                f"[Student File Repo] [Delete Application Documents] Error deleting application documents: {str(e)}"
            )
            raise
