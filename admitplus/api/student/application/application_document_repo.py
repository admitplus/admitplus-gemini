import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.database.mongo import BaseMongoCRUD


class ApplicationDocumentRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.application_document_collection = settings.APPLICATION_DOCUMENTS_COLLECTION
        logging.info(
            f"[Application Document Repo] Initialized with db: {self.db_name}, collection: {self.application_document_collection}"
        )

    async def add_application_document(
        self, application_document_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Add an application document to the database
        """
        try:
            insert_id = await self.mongo_repo.insert_one(
                document=application_document_data,
                collection_name=self.application_document_collection,
            )
            if insert_id:
                logging.info(
                    f"[Application Document Repo] [Add Document] Added document: {insert_id}"
                )
            return insert_id
        except Exception as e:
            logging.error(f"[Application Document Repo] [Add Document] Error: {str(e)}")
            return None

    async def find_application_documents_by_application_id(
        self, application_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find all documents for an application
        """
        try:
            logging.info(
                f"[Application Document Repo] [Find By Application] Finding documents for application: {application_id}"
            )

            result = await self.mongo_repo.find_many(
                query={"application_id": application_id},
                collection_name=self.application_document_collection,
            )
            logging.info(
                f"[Application Document Repo] [Find By Application] Found {len(result)} documents for application: {application_id}"
            )
            return result

        except Exception as e:
            logging.error(
                f"[Application Document Repo] [Find By Application] Error: {str(e)}"
            )
            return []

    async def find_application_document_by_app_doc_id(
        self, app_doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find application document by ID
        """
        try:
            logging.info(
                f"[Application Document Repo] [Find By ID] Finding application document: {app_doc_id}"
            )

            result = await self.mongo_repo.find_one(
                query={"app_doc_id": app_doc_id},
                collection_name=self.application_document_collection,
            )

            if result:
                logging.info(
                    f"[Application Document Repo] [Find By ID] Found application document: {app_doc_id}"
                )
            else:
                logging.warning(
                    f"[Application Document Repo] [Find By ID] Application document not found: {app_doc_id}"
                )

            return result

        except Exception as e:
            logging.error(f"[Application Document Repo] [Find By ID] Error: {str(e)}")
            return None

    async def delete_application_document_by_app_doc_id(self, app_doc_id: str) -> int:
        """
        Delete an application document by app_doc_id
        Returns the number of deleted documents (0 or 1)
        """
        try:
            logging.info(
                f"[Application Document Repo] [Delete Document] Deleting application document: {app_doc_id}"
            )

            deleted_count = await self.mongo_repo.delete_one(
                query={"app_doc_id": app_doc_id},
                collection_name=self.application_document_collection,
            )

            if deleted_count > 0:
                logging.info(
                    f"[Application Document Repo] [Delete Document] Successfully deleted application document: {app_doc_id}"
                )
            else:
                logging.warning(
                    f"[Application Document Repo] [Delete Document] Application document not found: {app_doc_id}"
                )

            return deleted_count

        except Exception as e:
            logging.error(
                f"[Application Document Repo] [Delete Document] Error: {str(e)}"
            )
            raise
