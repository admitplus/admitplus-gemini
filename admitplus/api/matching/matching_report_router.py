import logging
import traceback

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from typing import List

from admitplus.dependencies.role_check import get_current_user
from .matching_report_schema import MatchingReportRequest
from .matching_schema import MatchingResult, UniversitySearchFilter
from admitplus.common.response_schema import Response
from .matching_report_service import MatchingReportService

matching_report_service = MatchingReportService()

router = APIRouter(prefix="/matching/reports", tags=["Matching"])


@router.post("/{student_id}", response_model=Response[List[MatchingResult]])
async def generate_matching_report_handler(
    student_id: str = Path(..., description="Student ID"),
    university_ids: MatchingReportRequest = Body(
        ..., description="List of universities IDs (1-5)"
    ),
    current_user: dict = Depends(get_current_user),
):
    logging.info(
        f"[Matching Router] Processing request for student_id: {student_id}, university_ids: {university_ids.university_ids}"
    )
    try:
        result = await matching_report_service.generate_matching_report(
            student_id, university_ids.university_ids
        )
        logging.info(
            f"[Matching Router] Successfully processed request for student_id: {student_id}"
        )
        logging.info(
            f"[Matching Router] Result type: {type(result)}, length: {len(result) if isinstance(result, list) else 'N/A'}"
        )

        # Ensure result is a list
        if not isinstance(result, list):
            logging.warning(
                f"[Matching Router] Result is not a list, type: {type(result)}"
            )
            if isinstance(result, str):
                import json

                result = json.loads(result)

        if len(result) == 0:
            logging.warning(
                f"[Matching Router] WARNING: Empty result list returned for student_id: {student_id}"
            )

        return Response[List[MatchingResult]](
            code=200, message="Matching completed successfully", data=result
        )
    except HTTPException:
        raise
    except ValueError as e:
        logging.warning(
            f"[Matching Router] Validation error for student_id {student_id}: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Matching Router] Error processing request for student_id {student_id}: {str(e)}"
        )
        logging.error(f"[Matching Router] Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/{student_id}/{university_id}/{program_id}",
    response_model=Response[MatchingResult],
)
async def generate_university_match_insight_handler(
    student_id: str = Path(..., description="Student ID"),
    university_id: str = Path(..., description="University ID"),
    program_id: str = Path(..., description="Program ID"),
    current_user: dict = Depends(get_current_user),
):
    logging.info(
        f"[Matching Router] Processing request for student_id: {student_id}, university_id: {university_id}, program_id: {program_id}"
    )
    try:
        result = await matching_report_service.generate_university_match_insight(
            student_id, university_id, program_id
        )
        logging.info(
            f"[Matching Router] Successfully processed request for student_id: {student_id}, university_id: {university_id}, program_id: {program_id}"
        )
        return Response(
            code=200, message="Matching completed successfully", data=result
        )
    except HTTPException:
        raise
    except ValueError as e:
        logging.warning(
            f"[Matching Router] Validation error for student_id {student_id}, university_id {university_id}, program_id {program_id}: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Matching Router] Error processing request for student_id {student_id}, university_id {university_id}, program_id {program_id}: {str(e)}"
        )
        logging.error(f"[Matching Router] Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")
