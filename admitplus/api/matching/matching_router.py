import logging
import traceback

from fastapi import APIRouter, Body, Depends, HTTPException, Path

from admitplus.dependencies.role_check import get_current_user
from .matching_schema import (
    UniversitiesWithProgramsResult,
    UniversityWithPrograms,
    MatchingProgram,
    UniversitySearchFilter,
)
from admitplus.common.response_schema import Response
from .matching_service import MatchingService


matching_service = MatchingService()
router = APIRouter(prefix="/matching", tags=["Matching"])


@router.post("/{student_id}", response_model=Response[UniversitiesWithProgramsResult])
async def matching_handler(
    student_id: str = Path(..., description="Student ID"),
    request: UniversitySearchFilter = Body(
        ..., description="University search filter criteria"
    ),
    current_user: dict = Depends(get_current_user),
):
    logging.info(f"[Matching Router] Processing request for student_id: {student_id}")
    try:
        result = await matching_service.matching(request)
        programs = result.get("programs", [])

        # Group programs by university_id
        universities_map = {}
        for program in programs:
            university_id = program.get("university_id")
            if not university_id:
                continue

            if university_id not in universities_map:
                universities_map[university_id] = {
                    "university_id": university_id,
                    "university_name": program.get("university_name", ""),
                    "university_logo": program.get("university_logo"),
                    "programs": [],
                }

            # Create MatchingProgram object (without university_name and university_logo in nested programs)
            program_obj = MatchingProgram(
                program_id=program.get("program_id", ""),
                university_id=university_id,
                university_name=program.get("university_name", ""),
                university_logo=program.get("university_logo"),
            )
            universities_map[university_id]["programs"].append(program_obj)

        # Convert to list of UniversityWithPrograms
        universities_list = [
            UniversityWithPrograms(**univ_data)
            for univ_data in universities_map.values()
        ]

        universities_count = len(universities_list)
        programs_count = len(programs)
        logging.info(
            f"[Matching Router] Successfully processed request for student_id: {student_id}, found {programs_count} matching programs across {universities_count} universities"
        )

        return Response(
            code=200,
            message="Matching completed successfully",
            data=UniversitiesWithProgramsResult(universities=universities_list),
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[Matching Router] Error processing request for student_id {student_id}: {str(e)}"
        )
        logging.error(f"[Matching Router] Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")
