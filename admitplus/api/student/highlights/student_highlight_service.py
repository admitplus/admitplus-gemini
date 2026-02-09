import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import HTTPException

from .student_highlight_repo import StudentHighlightRepo
from ..schemas.student_schema import (
    StudentHighlightListResponse,
    StudentHighlightResponse,
    StudentHighlightCreateRequest,
    StudentHighlightUpdateRequest,
)
from admitplus.utils.crypto_utils import generate_uuid


class StudentHighlightService:
    def __init__(self):
        self.student_highlight_repo = StudentHighlightRepo()
        logging.info(f"[Student Highlight Service] Initialized with repository")

    async def create_student_highlight(
        self,
        student_id: str,
        created_by_member_id: str,
        request: StudentHighlightCreateRequest,
    ) -> StudentHighlightResponse:
        try:
            logging.info(
                f"[Student Highlight Service] [CreateStudentHighlight] Creating highlight for student_id: {student_id}, member_id: {created_by_member_id}"
            )

            highlight_id = generate_uuid()
            now = datetime.utcnow()

            highlight_data = request.model_dump(exclude_none=True)
            insert_id = await self.student_highlight_repo.create_student_highlight(
                student_id, created_by_member_id, highlight_id, highlight_data
            )

            if not insert_id:
                raise HTTPException(
                    status_code=500, detail="Failed to create student highlight"
                )

            logging.info(
                f"[Student Highlight Service] [CreateStudentHighlight] Successfully created highlight: {highlight_id}"
            )

            return StudentHighlightResponse(
                highlight_id=highlight_id,
                student_id=student_id,
                source_type=highlight_data.get("source_type", "manual"),
                source_id=highlight_data.get("source_id"),
                category=highlight_data["category"],
                text=highlight_data["text"],
                importance_score=highlight_data["importance_score"],
                tags=highlight_data.get("tags", []),
                created_by_member_id=created_by_member_id,
                created_at=now,
                updated_at=now,
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Highlight Service] [CreateStudentHighlight] Error creating student highlight: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to create student highlight"
            )

    async def create_highlights_from_parsed_result(
        self,
        student_id: str,
        items: List[Dict[str, Any]],
        created_by_member_id: str,
        source_id: Optional[str] = None,
        source_type: str = "file_analysis",
    ) -> int:
        """
        Create multiple student highlights from parsed file analysis results
        """
        try:
            logging.info(
                f"[Student Highlight Service] [CreateHighlightsFromParsedResult] Creating {len(items)} highlights for student_id: {student_id}"
            )

            created_count = 0

            for item in items:
                try:
                    # Validate required fields
                    if not item.get("category") or not item.get("text"):
                        logging.warning(
                            f"[Student Highlight Service] [CreateHighlightsFromParsedResult] Skipping invalid item: missing category or text"
                        )
                        continue

                    # Create highlight request from item
                    highlight_request = StudentHighlightCreateRequest(
                        category=item["category"],
                        text=item["text"],
                        importance_score=item.get("importance_score", 0.5),
                        tags=item.get("tags", []),
                        source_type=source_type,
                        source_id=source_id or item.get("source_id"),
                    )

                    # Create highlight
                    await self.create_student_highlight(
                        student_id=student_id,
                        created_by_member_id=created_by_member_id,
                        request=highlight_request,
                    )

                    created_count += 1

                except Exception as e:
                    logging.error(
                        f"[Student Highlight Service] [CreateHighlightsFromParsedResult] Error creating highlight from item: {str(e)}"
                    )
                    continue

            logging.info(
                f"[Student Highlight Service] [CreateHighlightsFromParsedResult] Successfully created {created_count} out of {len(items)} highlights"
            )
            return created_count

        except Exception as e:
            logging.error(
                f"[Student Highlight Service] [CreateHighlightsFromParsedResult] Error creating highlights from parsed result: {str(e)}"
            )
            return 0

    async def list_student_highlights(
        self,
        student_id: str,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> StudentHighlightListResponse:
        try:
            logging.info(
                f"[Student Highlight Service] [ListStudentHighlights] Listing highlights for student_id: {student_id}, page: {page}, page_size: {page_size}, category: {category}, q: {q}"
            )

            # Validate pagination parameters
            if page < 1:
                raise HTTPException(
                    status_code=400, detail="Page number must be greater than 0"
                )
            if page_size < 1 or page_size > 100:
                raise HTTPException(
                    status_code=400, detail="Page size must be between 1 and 100"
                )

            (
                highlight_dicts,
                total_count,
            ) = await self.student_highlight_repo.find_student_highlights(
                student_id, page, page_size, category, q
            )

            highlight_list = []
            for highlight_dict in highlight_dicts:
                try:
                    highlight = StudentHighlightResponse(**highlight_dict)
                    highlight_list.append(highlight)
                except Exception as e:
                    logging.warning(
                        f"[Student Highlight Service] [ListStudentHighlights] Skipping invalid highlight data: {str(e)}"
                    )
                    continue

            logging.info(
                f"[Student Highlight Service] [ListStudentHighlights] Successfully retrieved {len(highlight_list)}/{total_count} highlights for student_id: {student_id}"
            )
            return StudentHighlightListResponse(highlight_list=highlight_list)
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Highlight Service] [ListStudentHighlights] Error listing student highlights: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to list student highlights"
            )

    async def update_student_highlight(
        self, highlight_id: str, request: StudentHighlightUpdateRequest
    ) -> StudentHighlightResponse:
        """
        Update a student highlight
        """
        try:
            logging.info(
                f"[Student Highlight Service] [UpdateStudentHighlight] Updating highlight: {highlight_id}"
            )

            if not highlight_id or not highlight_id.strip():
                raise HTTPException(status_code=400, detail="Highlight ID is required")

            # Convert request to dict, excluding None values
            update_data = request.model_dump(exclude_none=True)

            if not update_data:
                raise HTTPException(
                    status_code=400,
                    detail="At least one field must be provided for update",
                )

            # Update the highlight
            updated_highlight_dict = (
                await self.student_highlight_repo.update_student_highlight(
                    highlight_id=highlight_id, highlight_data=update_data
                )
            )

            if not updated_highlight_dict:
                raise HTTPException(
                    status_code=404,
                    detail=f"Highlight not found with ID: {highlight_id}",
                )

            # Convert to response model
            result = StudentHighlightResponse(**updated_highlight_dict)

            logging.info(
                f"[Student Highlight Service] [UpdateStudentHighlight] Successfully updated highlight: {highlight_id}"
            )
            return result

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student Highlight Service] [UpdateStudentHighlight] Error updating highlight {highlight_id}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to update student highlight"
            )
