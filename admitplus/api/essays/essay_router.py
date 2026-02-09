import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query, status

from admitplus.dependencies.role_check import get_current_user
from .essay_draft_schema import (
    EssayDraftCreateRequest,
    EssayDraftListResponse,
    EssayDraftResponse,
)
from .essay_schema import (
    EssayCreateRequest,
    EssayDetailResponse,
    EssayListResponse,
    EssayUpdateRequest,
    EssayFinalizeRequest,
    EssayQuestionListResponse,
    GenerateEssayQuestionRequest,
    EssayQuestionUpdateRequest,
    EssayQuestionResponse,
)
from .essay_record_schema import (
    EssayGenerateRequest,
    EssayRecordDetailResponse,
    EssayRecordListResponse,
)
from admitplus.common.response_schema import Response
from .essay_service import EssayService
from admitplus.api.files.file_service import FileService


essay_service = EssayService()
file_service = FileService()

router = APIRouter(prefix="/essays", tags=["Essays"])


# ============================================================================
# Essay CRUD Endpoints
# ============================================================================


@router.post(
    "/applications/{application_id}/essay",
    response_model=Response[EssayDetailResponse],
    status_code=201,
)
async def create_essay_handler(
    application_id: str = Path(..., description="Application ID"),
    request: EssayCreateRequest = Body(..., description="Essay creation request"),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new essay for an application
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"""[Router] [CreateEssay] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [CreateEssay] Request received - application_id={application_id}, essay_type={request.essay_type}"""
    )
    try:
        result = await essay_service.create_essay(
            request=request,
            application_id=application_id,
            user_id=user_id,
        )
        logging.info(
            f"""[Router] [CreateEssay] Successfully created essay: {result.essay_id} (application_id={application_id}, essay_type={request.essay_type})"""
        )
        return Response(code=201, message="Essay created successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [CreateEssay] Validation error - application_id={application_id}, essay_type={request.essay_type}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [CreateEssay] Unexpected error - application_id={application_id}, essay_type={request.essay_type}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/applications/{application_id}/essays", response_model=Response[EssayListResponse]
)
async def get_application_essays_handler(
    application_id: str = Path(..., description="Application ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all essays for a given application
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(
            f"""[Router] [GetApplicationEssays] Missing user_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GetApplicationEssays] Request received - application_id={application_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.get_application_essays(
            application_id=application_id
        )
        logging.info(
            f"""[Router] [GetApplicationEssays] Successfully retrieved {len(result.items)} essay(s) for application_id={application_id}"""
        )
        return Response(code=200, message="Essays retrieved successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [GetApplicationEssays] Validation error - application_id={application_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GetApplicationEssays] Unexpected error - application_id={application_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{essay_id}", response_model=Response[EssayDetailResponse])
async def get_essay_detail_handler(
    essay_id: str = Path(..., description="Essay ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get essay detail by essay_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"""[Router] [GetEssayDetail] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GetEssayDetail] Request received - essay_id={essay_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.get_essay_detail(essay_id=essay_id)
        logging.info(
            f"""[Router] [GetEssayDetail] Successfully retrieved essay for essay_id={essay_id}"""
        )
        return Response(code=200, message="Essay retrieved successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [GetEssayDetail] Validation error - essay_id={essay_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GetEssayDetail] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{essay_id}", response_model=Response[EssayDetailResponse])
async def update_essay_handler(
    essay_id: str = Path(..., description="Essay ID"),
    request: EssayUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update essay by essay_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"""[Router] [UpdateEssay] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [UpdateEssay] Request received - essay_id={essay_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.update_essay_by_id(
            essay_id=essay_id, essay_data=request
        )
        logging.info(
            f"""[Router] [UpdateEssay] Successfully updated essay for essay_id={essay_id}"""
        )
        return Response(code=200, message="Essay updated successfully", data=result)
    except ValueError as e:
        logging.error(
            f"""[Router] [UpdateEssay] Validation error - essay_id={essay_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [UpdateEssay] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{essay_id}/finalize", response_model=Response[EssayDetailResponse])
async def finalize_essay_handler(
    essay_id: str = Path(..., description="Essay ID"),
    request: EssayFinalizeRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Finalize essay by essay_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"[Router] [FinalizeEssay] Missing user_id in current_user")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"[Router] [FinalizeEssay] Request received - essay_id={essay_id}, user_id={user_id}"
    )
    try:
        result = await essay_service.finalize_essay(
            essay_id=essay_id, final_draft_id=request.final_draft_id
        )
        logging.info(
            f"[Router] [FinalizeEssay] Successfully finalized essay for essay_id={essay_id}"
        )
        return Response(code=200, message="Essay finalized successfully", data=result)
    except ValueError as e:
        logging.error(
            f"[Router] [FinalizeEssay] Validation error - essay_id={essay_id}, error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Router] [FinalizeEssay] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{essay_id}/question_list", response_model=Response[EssayQuestionListResponse]
)
async def generate_essay_question_list_handler(
    essay_id: str = Path(..., description="Essay ID"),
    request: GenerateEssayQuestionRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate essay questions based on university, degree, title, and description
    """
    student_id = current_user.get("user_id")
    if not student_id:
        logging.error(
            f"[Router] [GenerateEssayQuestionList] Missing user_id in current_user"
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"[Router] [GenerateEssayQuestionList] Request received - essay_id={essay_id}, student_id={student_id}"
    )
    try:
        result = await essay_service.generate_essay_question_list(
            essay_id, request, student_id
        )
        logging.info(
            f"[Router] [GenerateEssayQuestionList] Successfully generated {len(result.items)} question(s) for essay_id={essay_id}"
        )
        return Response(
            code=200, message="Essay questions generated successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"[Router] [GenerateEssayQuestionList] Validation error - essay_id={essay_id}, error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Router] [GenerateEssayQuestionList] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/questions/{question_id}", response_model=Response[EssayQuestionResponse]
)
async def update_essay_question_handler(
    question_id: str = Path(..., description="Question ID"),
    request: EssayQuestionUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update essay question by question_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"[Router] [UpdateEssayQuestion] Missing user_id in current_user")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"[Router] [UpdateEssayQuestion] Request received - question_id={question_id}, user_id={user_id}"
    )
    try:
        result = await essay_service.update_essay_question(
            question_id=question_id, question_text=request.question
        )
        logging.info(
            f"[Router] [UpdateEssayQuestion] Successfully updated question for question_id={question_id}"
        )
        return Response(
            code=200, message="Essay question updated successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"[Router] [UpdateEssayQuestion] Validation error - question_id={question_id}, error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Router] [UpdateEssayQuestion] Unexpected error - question_id={question_id}, error: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{essay_id}/questions", response_model=Response[EssayQuestionListResponse])
async def get_essay_questions_handler(
    essay_id: str = Path(..., description="Essay ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all essay questions for a given essay_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"[Router] [GetEssayQuestions] Missing user_id in current_user")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"[Router] [GetEssayQuestions] Request received - essay_id={essay_id}, user_id={user_id}"
    )
    try:
        result = await essay_service.get_essay_questions_by_essay_id(essay_id=essay_id)
        logging.info(
            f"[Router] [GetEssayQuestions] Successfully retrieved {len(result.items)} question(s) for essay_id={essay_id}"
        )
        return Response(
            code=200, message="Essay questions retrieved successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"[Router] [GetEssayQuestions] Validation error - essay_id={essay_id}, error: {e}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Router] [GetEssayQuestions] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Essay Draft Endpoints
# ============================================================================


@router.get("/{essay_id}/drafts", response_model=Response[EssayDraftListResponse])
async def list_essay_drafts_handler(
    essay_id: str = Path(..., description="Essay ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all essay drafts for a given essay_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"""[Router] [ListEssayDrafts] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [ListEssayDrafts] Request received - essay_id={essay_id}, user_id={user_id}, page={page}, page_size={page_size}"""
    )
    try:
        result = await essay_service.list_essay_drafts(
            essay_id=essay_id, page=page, page_size=page_size
        )
        logging.info(
            f"""[Router] [ListEssayDrafts] Successfully retrieved {len(result.items)} draft(s) for essay_id={essay_id}"""
        )
        return Response(
            code=200, message="Essay drafts retrieved successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"""[Router] [ListEssayDrafts] Validation error - essay_id={essay_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [ListEssayDrafts] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{essay_id}/draft", response_model=Response[EssayDraftResponse], status_code=201
)
async def create_essay_draft_handler(
    essay_id: str = Path(..., description="Essay ID"),
    request: EssayDraftCreateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new essay draft for a given essay_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(
            f"""[Router] [CreateEssayDraft] Missing user_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [CreateEssayDraft] Request received - essay_id={essay_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.create_essay_draft(
            essay_id=essay_id, request=request, user_id=user_id
        )
        logging.info(
            f"""[Router] [CreateEssayDraft] Successfully created draft with draft_id={result.draft_id} for essay_id={essay_id}"""
        )
        return Response(
            code=201, message="Essay draft created successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"""[Router] [CreateEssayDraft] Validation error - essay_id={essay_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [CreateEssayDraft] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/draft/{draft_id}", response_model=Response[EssayDraftResponse])
async def get_draft_detail_handler(
    draft_id: str = Path(..., description="Draft ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get essay draft detail by draft_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(f"""[Router] [GetDraftDetail] Missing user_id in current_user""")
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GetDraftDetail] Request received - draft_id={draft_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.get_draft_detail(draft_id=draft_id)
        logging.info(
            f"""[Router] [GetDraftDetail] Successfully retrieved draft for draft_id={draft_id}"""
        )
        return Response(
            code=200, message="Essay draft retrieved successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"""[Router] [GetDraftDetail] Validation error - draft_id={draft_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GetDraftDetail] Unexpected error - draft_id={draft_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Essay
# ============================================================================


@router.post(
    "/{essay_id}/generate",
    response_model=Response[EssayRecordDetailResponse],
    status_code=201,
)
async def generate_essay_draft_handler(
    essay_id: str = Path(..., description="Essay ID"),
    request: EssayGenerateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a new essay draft for a given essay_id
    Creates a draft in essay_drafts collection and saves request/response in essay_records collection
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(
            f"""[Router] [GenerateEssayDraft] Missing user_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GenerateEssayDraft] Request received - essay_id={essay_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.generate_essay_draft(
            essay_id=essay_id, request=request, user_id=user_id
        )
        logging.info(
            f"""[Router] [GenerateEssayDraft] Successfully generated draft with draft_id={result.draft_id} and record_id={result.record_id} for essay_id={essay_id}"""
        )
        return Response(
            code=201, message="Essay draft generated successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"""[Router] [GenerateEssayDraft] Validation error - essay_id={essay_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GenerateEssayDraft] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{essay_id}/records", response_model=Response[EssayRecordListResponse])
async def list_essay_records_handler(
    essay_id: str = Path(..., description="Essay ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    List all essay records for a given essay_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(
            f"""[Router] [ListEssayRecords] Missing user_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [ListEssayRecords] Request received - essay_id={essay_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.list_essay_records(essay_id=essay_id)
        logging.info(
            f"""[Router] [ListEssayRecords] Successfully retrieved {len(result.items)} record(s) for essay_id={essay_id}"""
        )
        return Response(
            code=200, message="Essay records retrieved successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"""[Router] [ListEssayRecords] Validation error - essay_id={essay_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [ListEssayRecords] Unexpected error - essay_id={essay_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/essay-record/{record_id}", response_model=Response[EssayRecordDetailResponse]
)
async def get_essay_record_detail_handler(
    record_id: str = Path(..., description="Record ID"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get essay record detail by record_id
    """
    user_id = current_user.get("user_id")
    if not user_id:
        logging.error(
            f"""[Router] [GetEssayRecordDetail] Missing user_id in current_user"""
        )
        raise HTTPException(status_code=400, detail="Invalid user information")

    logging.info(
        f"""[Router] [GetEssayRecordDetail] Request received - record_id={record_id}, user_id={user_id}"""
    )
    try:
        result = await essay_service.get_essay_record_detail(record_id=record_id)
        logging.info(
            f"""[Router] [GetEssayRecordDetail] Successfully retrieved record with record_id={record_id}"""
        )
        return Response(
            code=200, message="Essay record retrieved successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"""[Router] [GetEssayRecordDetail] Validation error - record_id={record_id}, error: {e}"""
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"""[Router] [GetEssayRecordDetail] Unexpected error - record_id={record_id}, error: {e}\n{traceback.format_exc()}"""
        )
        raise HTTPException(status_code=500, detail="Internal server error")
