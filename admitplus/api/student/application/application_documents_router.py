import logging
import traceback

from fastapi import APIRouter, Depends, Body, Path, HTTPException

from admitplus.api.student.schemas.application.application_documents_schema import (
    ApplicationDocumentResponse,
    ApplicationDocumentCreateRequest,
    ApplicationDocumentListResponse,
)
from admitplus.common.response_schema import Response
from admitplus.dependencies.role_check import get_current_user

from admitplus.api.student.application.application_documents_service import (
    ApplicationDocumentService,
)


application_document_service = ApplicationDocumentService()
router = APIRouter(prefix="/applications", tags=["Application Documents"])


@router.post(
    "/{application_id}/documents", response_model=Response[ApplicationDocumentResponse]
)
async def add_application_document_handler(
    application_id: str = Path(..., description="Application ID"),
    request: ApplicationDocumentCreateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Add a document (resume/sop/lor) to an application
    """
    logging.info(
        f"[Application Document Router] [Add Document] Request received for application {application_id}"
    )
    try:
        result = await application_document_service.add_application_document(
            application_id=application_id, request=request
        )
        logging.info(
            f"[Application Document Router] [Add Document] Successfully added document {result.app_doc_id} to application {application_id}"
        )
        return Response(
            code=201, message="Application document added successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Application Document Router] [Add Document] Error: {str(e)}")
        logging.error(
            f"[Application Document Router] [Add Document] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while adding application document",
        )


@router.get(
    "/{application_id}/documents",
    response_model=Response[ApplicationDocumentListResponse],
)
async def get_application_document_handler(
    application_id: str = Path(..., description="Application ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all documents for an application
    """
    logging.info(
        f"[Application Document Router] [Get Documents] Getting documents for application {application_id}"
    )
    try:
        result = await application_document_service.get_application_documents(
            application_id=application_id
        )
        logging.info(
            f"[Application Document Router] [Get Documents] Successfully retrieved {len(result.items)} documents for application {application_id}"
        )
        return Response(
            code=200,
            message="Application documents retrieved successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Application Document Router] [Get Documents] Error: {str(e)}")
        logging.error(
            f"[Application Document Router] [Get Documents] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while retrieving application documents",
        )


@router.delete(
    "/application-documents/{app_doc_id}",
    response_model=Response[ApplicationDocumentResponse],
)
async def delete_application_document_handler(
    app_doc_id: str = Path(..., description="Application Document ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an application document by app_doc_id
    """
    logging.info(
        f"[Application Document Router] [Delete Document] Deleting application document {app_doc_id}"
    )
    try:
        result = await application_document_service.delete_application_document(
            app_doc_id=app_doc_id
        )
        logging.info(
            f"[Application Document Router] [Delete Document] Successfully deleted document {app_doc_id}"
        )
        return Response(
            code=200, message="Application document deleted successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Application Document Router] [Delete Document] Error: {str(e)}"
        )
        logging.error(
            f"[Application Document Router] [Delete Document] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error while deleting application document",
        )
