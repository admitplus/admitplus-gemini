import logging
import traceback
from datetime import datetime

from fastapi import HTTPException

from .application_document_repo import ApplicationDocumentRepo
from .application_repo import ApplicationRepo
from admitplus.api.files.file_metadata_repo import FileRepo
from admitplus.api.student.schemas.application.application_documents_schema import (
    ApplicationDocumentCreateRequest,
    ApplicationDocumentResponse,
    ApplicationDocumentListResponse,
)
from admitplus.utils.crypto_utils import generate_uuid


class ApplicationDocumentService:
    def __init__(self):
        self.application_document_repo = ApplicationDocumentRepo()
        self.application_repo = ApplicationRepo()
        self.file_repo = FileRepo()
        logging.info(f"[Application Document Service] Initialized")

    async def add_application_document(
        self,
        application_id: str,
        request: ApplicationDocumentCreateRequest,
    ) -> ApplicationDocumentResponse:
        """
        Add a document (resume/sop/lor) to an application
        """
        try:
            logging.info(
                f"[Application Document Service] [Add Document] Adding document to application {application_id}"
            )

            if not application_id or not application_id.strip():
                raise HTTPException(
                    status_code=400, detail="Application ID is required"
                )

            # Validate that application exists
            application = await self.application_repo.find_application_by_id(
                application_id
            )
            if not application:
                raise HTTPException(status_code=404, detail="Application not found")

            # Validate that file exists
            file_metadata = await self.file_repo.find_file_by_id(request.file_id)
            if not file_metadata:
                raise HTTPException(status_code=404, detail="File not found")

            # Prepare application document data
            now = datetime.utcnow()
            app_doc_id = generate_uuid()
            application_document_data = {
                "app_doc_id": app_doc_id,
                "application_id": application_id.strip(),
                "file_id": request.file_id,
                "usage": request.usage,
                "note": request.note,
                "created_at": now,
                "updated_at": now,
            }

            insert_id = await self.application_document_repo.add_application_document(
                application_document_data
            )
            if not insert_id:
                logging.error(
                    f"[Application Document Service] [Add Document] Failed to add document for application {application_id}"
                )
                raise HTTPException(
                    status_code=500, detail="Failed to add application document"
                )

            logging.info(
                f"[Application Document Service] [Add Document] Successfully added document {app_doc_id} to application {application_id}"
            )
            return ApplicationDocumentResponse(**application_document_data)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Document Service] [Add Document] Error adding document to application {application_id}: {str(e)}"
            )
            logging.error(
                f"[Application Document Service] [Add Document] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to add application document"
            )

    async def get_application_documents(
        self,
        application_id: str,
    ) -> ApplicationDocumentListResponse:
        """
        Get all documents for an application
        """
        try:
            documents = await self.application_document_repo.find_application_documents_by_application_id(
                application_id
            )
            items = [ApplicationDocumentResponse(**doc) for doc in documents]
            return ApplicationDocumentListResponse(items=items)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Document Service] [Get Documents] Error getting documents for application {application_id}: {str(e)}"
            )
            logging.error(
                f"[Application Document Service] [Get Documents] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to get application documents"
            )

    async def delete_application_document(
        self,
        app_doc_id: str,
    ) -> ApplicationDocumentResponse:
        """
        Delete an application document by app_doc_id
        """
        try:
            logging.info(
                f"[Application Document Service] [Delete Document] Deleting application document {app_doc_id}"
            )

            if not app_doc_id or not app_doc_id.strip():
                raise HTTPException(
                    status_code=400, detail="Application Document ID is required"
                )

            # Check if document exists before deletion
            document = await self.application_document_repo.find_application_document_by_app_doc_id(
                app_doc_id
            )
            if not document:
                raise HTTPException(
                    status_code=404, detail="Application document not found"
                )

            # Delete the document
            deleted_count = await self.application_document_repo.delete_application_document_by_app_doc_id(
                app_doc_id
            )
            if deleted_count == 0:
                logging.error(
                    f"[Application Document Service] [Delete Document] Failed to delete document {app_doc_id}"
                )
                raise HTTPException(
                    status_code=500, detail="Failed to delete application document"
                )

            logging.info(
                f"[Application Document Service] [Delete Document] Successfully deleted document {app_doc_id}"
            )
            return ApplicationDocumentResponse(**document)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Document Service] [Delete Document] Error deleting document {app_doc_id}: {str(e)}"
            )
            logging.error(
                f"[Application Document Service] [Delete Document] Stack trace: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to delete application document"
            )
