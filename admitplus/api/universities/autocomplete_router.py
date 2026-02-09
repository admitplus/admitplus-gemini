import logging
import traceback

from fastapi import APIRouter, HTTPException, Query

from .suggestion_schema import ProgramSuggestionsResponse, UniversitySuggestionsResponse
from admitplus.common.response_schema import Response
from .information_service import InformationService
from .suggestion_service import SuggestionService


suggestion_service = SuggestionService()
information_service = InformationService()

router = APIRouter(prefix="/universities", tags=["autocomplete"])


@router.get("/autocomplete", response_model=Response[UniversitySuggestionsResponse])
async def university_autocomplete_handler(
    query: str = Query(
        ..., min_length=1, description="University name search keywords"
    ),
    country_code: str = Query(
        None, description="Filter by country code (e.g., US, CA, UK)"
    ),
):
    """
    Get universities name suggestions for autocomplete functionality (lightweight results)
    """
    try:
        logging.info(
            f"[Router] [UniversityAutocomplete] Starting request - query='{query}', country_code='{country_code}'"
        )

        result = await suggestion_service.university_autocomplete(
            query=query, country_code=country_code
        )

        logging.info(
            f"[Router] [UniversityAutocomplete] Success - found {len(result)} suggestions for query='{query}', country_code='{country_code}'"
        )
        return Response(
            code=200,
            message="University autocomplete retrieved successfully",
            data={"suggestions": result},
        )
    except Exception as e:
        logging.error(
            f"[Router] [UniversityAutocomplete] Error - query='{query}', country_code='{country_code}', error={str(e)}"
        )
        logging.error(
            f"[Router] [UniversityAutocomplete] Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/programs/autocomplete", response_model=Response[ProgramSuggestionsResponse]
)
async def programs_autocomplete_handler(
    degree: str = Query(..., description="Degree name (bachelor, master, phd)"),
    query: str = Query(..., min_length=3),
):
    """
    Get program name suggestions for autocomplete functionality
    """
    try:
        logging.info(
            f"[Router] [ProgramAutocomplete] Starting request - degree={degree}, query='{query}'"
        )
        result = await suggestion_service.program_suggestions(degree, query)

        logging.info(
            f"[Router] [ProgramAutocomplete] Success - found {len(result)} suggestions for degree={degree}, query='{query}'"
        )
        return Response(
            code=200,
            message="Program autocomplete retrieved successfully",
            data={"suggestions": result},
        )
    except ValueError as e:
        logging.error(f"[Router] [ProgramAutocomplete] Bad request - {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Router] [ProgramAutocomplete] Error - degree={degree}, query='{query}', error={str(e)}"
        )
        logging.error(
            f"[Router] [ProgramAutocomplete] Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{university_id}/programs", response_model=Response[ProgramSuggestionsResponse]
)
async def university_programs_autocomplete_handler(
    university_id: str,
    degree: str = Query(..., description="Degree name (bachelor, master, phd)"),
    query: str = Query(..., min_length=3, description="Program name search keywords"),
):
    """
    Get program autocomplete results for a known universities (by ID),
    filtered by degree and prefix query
    """
    try:
        logging.info(
            f"[Router] [ProgramAutocompleteByUniversity] Start - university_id={university_id}, degree={degree}, query='{query}'"
        )
        result = await suggestion_service.search_programs(
            query=query, university_id=university_id, degree_level=degree
        )
        logging.info(
            f"[Router] [ProgramAutocompleteByUniversity] Success - found {len(result)} suggestions"
        )
        return Response(
            code=200,
            message="Program autocomplete retrieved successfully",
            data={"suggestions": result},
        )
    except ValueError as e:
        logging.error(
            f"[Router] [ProgramAutocompleteByUniversity] Bad request - {str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(
            f"[Router] [ProgramAutocompleteByUniversity] Error - university_id={university_id}, degree={degree}, query='{query}', error={str(e)}"
        )
        logging.error(
            f"[Router] [ProgramAutocompleteByUniversity] Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
