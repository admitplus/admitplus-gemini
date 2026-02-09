import logging
import traceback
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from admitplus.common.response_schema import Response
from .information_schema import (
    UniversityProgramQueryRequest,
    UniversityProgramResponse,
    UniversitiesByMajorRequest,
    UniversitiesByMajorResponse,
    UniversitySearchResponse,
)
from .university_service import UniversityService
from .information_service import InformationService

university_service = UniversityService()
information_service = InformationService()

router = APIRouter(prefix="/universities", tags=["University"])


@router.get("/search", response_model=Response[UniversitySearchResponse])
async def search_universities_handler(
    university_name: str = Query(
        ..., min_length=1, description="Search query for university name"
    ),
    country: Optional[str] = Query(
        None, description="Filter by country code (e.g., US, CA, UK)"
    ),
    degree_level: Optional[str] = Query(
        None, description="Filter by degree level (undergrad, graduate, phd)"
    ),
) -> Response[UniversitySearchResponse]:
    """
    Search universities by name with optional filters for country and degree level.
    Returns detailed university information.
    """
    logging.info(
        f"[University Router] [SearchUniversities] Request received - university_name: {university_name}, country: {country}, degree_level: {degree_level}"
    )

    try:
        # Call service
        logging.info(
            f"[University Router] [SearchUniversities] Calling service with university_name: {university_name}, country: {country}, degree_level: {degree_level}"
        )
        result = await information_service.search_universities(
            query=university_name, country=country, degree_level=degree_level
        )

        # Log success
        university_count = (
            len(result.get("universities", [])) if isinstance(result, dict) else 0
        )
        logging.info(
            f"[University Router] [SearchUniversities] Successfully retrieved {university_count} universities for query: {university_name}"
        )
        return Response(
            code=200, message="Universities search completed successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"[University Router] [SearchUniversities] Validation/Value error - university_name: {university_name}, country: {country}, degree_level: {degree_level}, error: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [SearchUniversities] Unexpected error - university_name: {university_name}, country: {country}, degree_level: {degree_level}, error: {str(e)}"
        )
        logging.error(
            f"[University Router] [SearchUniversities] Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/programs", response_model=Response[UniversityProgramResponse])
async def get_program_details_handler(
    country: str = Query(..., description="Country name"),
    university_id: str = Query(..., description="University ID"),
    degree: str = Query(..., description="Degree type: undergraduate|graduate|phd"),
    program_name: str = Query(..., description="Program name"),
):
    """
    Get detailed information about a specific universities program
    """
    logging.info(
        f"[University Router] [GetProgramDetails] Request received - country: {country}, university_id: {university_id}, degree: {degree}, program_name: {program_name}"
    )

    try:
        # Validate and create request object
        logging.debug(
            f"[University Router] [GetProgramDetails] Creating request object"
        )
        request = UniversityProgramQueryRequest(
            country=country,
            university_id=university_id,
            degree=degree,
            program_name=program_name,
        )
        logging.debug(
            f"[University Router] [GetProgramDetails] Request object created successfully"
        )

        # Call service
        logging.info(
            f"[University Router] [GetProgramDetails] Calling service with university_id: {university_id}, degree: {degree}, program_name: {program_name}"
        )
        result = await information_service.get_program_details(request)

        # Log success
        logging.info(
            f"[University Router] [GetProgramDetails] Successfully retrieved program details for university_id: {university_id}, program_name: {program_name}"
        )
        return Response(
            code=200, message="University details retrieved successfully", data=result
        )

    except ValueError as e:
        logging.error(
            f"[University Router] [GetProgramDetails] Validation/Value error - university_id: {university_id}, degree: {degree}, program_name: {program_name}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions (like 404, 400, etc.)
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [GetProgramDetails] Unexpected error - university_id: {university_id}, degree: {degree}, program_name: {program_name}, error: {str(e)}"
        )
        logging.error(
            f"[University Router] [GetProgramDetails] Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/by-major", response_model=Response[UniversitiesByMajorResponse])
async def list_universities_by_major_handler(
    country: str = Query(..., description="Country name"),
    program_name: str = Query(..., description="Program name"),
    degree: str = Query(..., description="Degree type: undergraduate|graduate|phd"),
) -> Response[UniversitiesByMajorResponse]:
    """
    Get list of universities that offer a specific program and degree
    """
    logging.info(
        f"[University Router] [ListUniversitiesByProgram] Request received - country: {country}, program_name: {program_name}, degree: {degree}"
    )

    try:
        # Validate and create request object
        logging.debug(
            f"[University Router] [ListUniversitiesByProgram] Creating request object"
        )
        request = UniversitiesByMajorRequest(
            country=country, program_name=program_name, degree=degree
        )
        logging.debug(
            f"[University Router] [ListUniversitiesByProgram] Request object created successfully"
        )

        # Call service
        logging.info(
            f"[University Router] [ListUniversitiesByProgram] Calling service with program_name: {program_name}, degree: {degree}"
        )
        result = await information_service.list_universities_by_major(request)

        # Log success with count
        university_count = (
            len(result.get("university_list", [])) if isinstance(result, dict) else 0
        )
        logging.info(
            f"[University Router] [ListUniversitiesByProgram] Successfully retrieved {university_count} universities(ies) for program_name: {program_name}, degree: {degree}"
        )
        return Response(
            code=200,
            message="Universities by program retrieved successfully",
            data=result,
        )
    except ValueError as e:
        logging.error(
            f"[University Router] [ListUniversitiesByProgram] Validation/Value error - country: {country}, program_name: {program_name}, degree: {degree}, error: {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [ListUniversitiesByProgram] Unexpected error - country: {country}, program_name: {program_name}, degree: {degree}, error: {str(e)}"
        )
        logging.error(
            f"[University Router] [ListUniversitiesByProgram] Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


# University detail endpoints (using path parameters)
@router.get("/{university_id}/profile", response_model=Response[dict])
async def find_university_profile_handler(
    university_id: str = Path(..., description="University ID"),
):
    """
    Get universities profile by universities ID
    """
    logging.info(
        f"[University Router] [Find University Profile] Processing request for university_id: {university_id}"
    )
    try:
        result = await university_service.find_university_profile(university_id)

        if not result:
            logging.warning(
                f"[University Router] [Find University Profile] University profile not found: {university_id}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"University profile not found for ID: {university_id}",
            )

        logging.info(
            f"[University Router] [Find University Profile] Successfully retrieved universities profile: {university_id}"
        )
        return Response(
            code=200, message="University profile retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [Find University Profile] Error processing request for university_id {university_id}: {str(e)}"
        )
        logging.error(
            f"[University Router] [Find University Profile] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{university_id}/program/{program_id}", response_model=Response[dict])
async def find_program_profile_handler(
    university_id: str = Path(..., description="University ID"),
    program_id: str = Path(..., description="Program ID"),
):
    """
    Get program profile by universities ID and program ID
    """
    logging.info(
        f"[University Router] [Find Program Profile] Processing request for university_id: {university_id}, program_id: {program_id}"
    )
    try:
        result = await university_service.find_program_profile(
            university_id, program_id
        )

        if not result:
            logging.warning(
                f"[University Router] [Find Program Profile] Program profile not found: university_id={university_id}, program_id={program_id}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Program profile not found for university_id: {university_id}, program_id: {program_id}",
            )

        logging.info(
            f"[University Router] [Find Program Profile] Successfully retrieved program profile: university_id={university_id}, program_id={program_id}"
        )
        return Response(
            code=200, message="Program profile retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [Find Program Profile] Error processing request for university_id {university_id}, program_id {program_id}: {str(e)}"
        )
        logging.error(
            f"[University Router] [Find Program Profile] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{university_id}/admission-cycle", response_model=Response[dict])
async def find_admission_cycle_handler(
    university_id: str = Path(..., description="University ID"),
    study_level: str = Query(
        ..., description="Study level (e.g., undergraduate, graduate, phd)"
    ),
):
    """
    Get admission cycle by universities ID and study level
    """
    logging.info(
        f"[University Router] [Find Admission Cycle] Processing request for university_id: {university_id}, study_level: {study_level}"
    )
    try:
        result = await university_service.find_admission_cycle(
            university_id, study_level
        )

        if not result:
            logging.warning(
                f"[University Router] [Find Admission Cycle] Admission cycle not found: university_id={university_id}, study_level={study_level}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Admission cycle not found for university_id: {university_id}, study_level: {study_level}",
            )

        logging.info(
            f"[University Router] [Find Admission Cycle] Successfully retrieved admission cycle: university_id={university_id}, study_level={study_level}"
        )
        return Response(
            code=200, message="Admission cycle retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [Find Admission Cycle] Error processing request for university_id {university_id}, study_level {study_level}: {str(e)}"
        )
        logging.error(
            f"[University Router] [Find Admission Cycle] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{university_id}/admission-requirements", response_model=Response[dict])
async def find_admission_requirements_handler(
    university_id: str = Path(..., description="University ID"),
    degree_level: str = Query(
        ..., description="Degree level (e.g., Undergraduate, Graduate, PhD)"
    ),
):
    """
    Get admission requirements by universities ID and degree level
    """
    logging.info(
        f"[University Router] [Find Admission Requirements] Processing request for university_id: {university_id}, degree_level: {degree_level}"
    )
    try:
        result = await university_service.find_admission_requirements(
            university_id, degree_level
        )

        if not result:
            logging.warning(
                f"[University Router] [Find Admission Requirements] Admission requirements not found: university_id={university_id}, degree_level={degree_level}"
            )
            raise HTTPException(
                status_code=404,
                detail=f"Admission requirements not found for university_id: {university_id}, degree_level: {degree_level}",
            )

        logging.info(
            f"[University Router] [Find Admission Requirements] Successfully retrieved admission requirements: university_id={university_id}, degree_level={degree_level}"
        )
        return Response(
            code=200,
            message="Admission requirements retrieved successfully",
            data=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [Find Admission Requirements] Error processing request for university_id {university_id}, degree_level {degree_level}: {str(e)}"
        )
        logging.error(
            f"[University Router] [Find Admission Requirements] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{university_id}", response_model=Response[dict])
async def get_university_detail_handler(
    university_id: str = Path(
        ..., min_length=1, description="University ID to get detailed information"
    ),
    study_level: str = Query(
        ..., description="Study level (e.g., undergraduate, graduate, phd)"
    ),
) -> Response[dict]:
    """
    Get detailed information about a specific university by university_id.
    Returns detailed university information.
    """
    logging.info(
        f"[University Router] [GetUniversityDetail] Request received - university_id: {university_id}, study_level: {study_level}"
    )

    try:
        # Call service
        logging.info(
            f"[University Router] [GetUniversityDetail] Calling service with university_id: {university_id}, study_level: {study_level}"
        )
        result = await information_service.get_university_detail(
            university_id=university_id, study_level=study_level
        )

        # Log success
        university_name = (
            result.get("university_name", "Unknown")
            if isinstance(result, dict)
            else "Unknown"
        )
        logging.info(
            f"[University Router] [GetUniversityDetail] Successfully retrieved university details for university_id: {university_id}, name: {university_name}, study_level: {study_level}"
        )
        return Response(
            code=200, message="University details retrieved successfully", data=result
        )
    except ValueError as e:
        logging.error(
            f"[University Router] [GetUniversityDetail] Validation/Value error - university_id: {university_id}, study_level: {study_level}, error: {str(e)}"
        )
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(
            f"[University Router] [GetUniversityDetail] Unexpected error - university_id: {university_id}, study_level: {study_level}, error: {str(e)}"
        )
        logging.error(
            f"[University Router] [GetUniversityDetail] Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
