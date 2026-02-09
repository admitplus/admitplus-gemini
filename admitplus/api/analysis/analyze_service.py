import logging
import traceback
import math
from typing import Dict, Any, List, Tuple, Optional

from admitplus.api.files.file_service import FileService
from admitplus.api.files.file_schema import FileMetadata
from admitplus.utils.content_extractor import content_extractor
from admitplus.llm.prompts.gpt_prompts.analyze_prompt.student_file_extract_prompt import (
    build_student_file_extract_prompt,
)
from admitplus.llm.providers.openai.openai_client import (
    generate_text as openai_generate_text,
)
from admitplus.llm.llm_utils import parse_llm_json_response
from admitplus.api.student.repos.student_profile_repo import StudentRepo
from admitplus.api.student.repos.student_assignment_repo import StudentAssignmentRepo
from admitplus.api.agency.agency_member_repo import AgencyMemberRepo


class AnalysisService:
    def __init__(self):
        self.file_service = FileService()
        self.student_repo = StudentRepo()
        self.student_assignment_repo = StudentAssignmentRepo()
        self.agency_member_repo = AgencyMemberRepo()

    async def analyze_file(
        self, file_metadata: FileMetadata, mode: str = "standard"
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Analyze a file and extract text and highlights
        """
        logging.info(
            f"[File Analysis Service] [Analyze File] Starting analysis for file: {file_metadata.file_id}, mode: {mode}"
        )

        try:
            # 1. Download file content to memory
            file_content = await self.file_service.download_file_to_memory(
                file_metadata.file_id
            )

            if file_content is None:
                raise ValueError(
                    f"Failed to download file content for file_id: {file_metadata.file_id}"
                )

            logging.info(
                f"[File Analysis Service] [Analyze File] Downloaded file content: {len(file_content)} bytes"
            )

            # 2. Extract text from file
            extraction_result = content_extractor.extract_text(
                file_content=file_content,
                file_name=file_metadata.file_name,
                content_type=file_metadata.content_type,
            )

            parsed_text = extraction_result.get("extracted_text", "")
            logging.info(
                f"[File Analysis Service] [Analyze File] Extracted text length: {len(parsed_text)} characters"
            )

            # 3. Generate highlights from parsed text (basic implementation)
            # This can be enhanced with LLM-based extraction in the future
            highlight_items = self._generate_highlights_from_text(
                parsed_text, file_metadata, mode
            )

            logging.info(
                f"[File Analysis Service] [Analyze File] Generated {len(highlight_items)} highlight items"
            )

            return parsed_text, highlight_items

        except Exception as e:
            logging.error(
                f"[File Analysis Service] [Analyze File] Error analyzing file {file_metadata.file_id}: {str(e)}"
            )
            raise

    def _generate_highlights_from_text(
        self, text: str, file_metadata: FileMetadata, mode: str
    ) -> List[Dict[str, Any]]:
        """
        Generate highlight items from extracted text
        """
        highlight_items = []

        if not text or len(text.strip()) == 0:
            return highlight_items

        # Basic implementation: extract key information based on file type
        # This can be enhanced with LLM-based extraction
        file_type = file_metadata.file_type

        # For now, return empty list - highlights can be created manually or via LLM
        # In a full implementation, this would use LLM to extract key information
        # and create structured highlight items

        logging.info(
            f"[File Analysis Service] [Generate Highlights] Generated {len(highlight_items)} highlights for file type: {file_type}"
        )

        return highlight_items

    async def analyze_student_file(
        self, file_metadata: FileMetadata, mode: str = "standard"
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Analyze a student file using LLM to extract student profile and highlights

        Returns:
            Tuple of (parsed_text, student_profile_data, highlight_items)
        """
        logging.info(
            f"[Analysis Service] [Analyze Student File] Starting LLM analysis for file: {file_metadata.file_id}, mode: {mode}"
        )

        try:
            # 1. Download file content to memory
            file_content = await self.file_service.download_file_to_memory(
                file_metadata.file_id
            )

            if file_content is None:
                raise ValueError(
                    f"Failed to download file content for file_id: {file_metadata.file_id}"
                )

            logging.info(
                f"[Analysis Service] [Analyze Student File] Downloaded file content: {len(file_content)} bytes"
            )

            # 2. Extract text from file
            extraction_result = content_extractor.extract_text(
                file_content=file_content,
                file_name=file_metadata.file_name,
                content_type=file_metadata.content_type,
            )

            parsed_text = extraction_result.get("extracted_text", "")
            logging.info(
                f"[Analysis Service] [Analyze Student File] Extracted text length: {len(parsed_text)} characters"
            )

            if not parsed_text or len(parsed_text.strip()) == 0:
                logging.warning(
                    f"[Analysis Service] [Analyze Student File] No text extracted from file {file_metadata.file_id}"
                )
                return parsed_text, {}, []

            # 3. Call LLM to extract student profile and highlights
            logging.info(
                f"[Analysis Service] [Analyze Student File] Calling LLM to extract student information"
            )
            messages = build_student_file_extract_prompt(parsed_text)

            llm_response = await openai_generate_text(
                messages=messages, temperature=0.3, max_tokens=4000
            )

            logging.info(
                f"[Analysis Service] [Analyze Student File] Received LLM response: {len(llm_response)} characters"
            )

            # 4. Parse LLM JSON response
            extracted_data = parse_llm_json_response(
                llm_response, context="[Analysis Service] [Analyze Student File]"
            )

            logging.info(
                f"[Analysis Service] [Analyze Student File] Successfully parsed LLM response"
            )

            # 5. Extract student profile data (matching new schema structure)
            student_profile_data = {}

            # Extract stage
            if "stage" in extracted_data:
                student_profile_data["stage"] = extracted_data["stage"]

            # Extract basic_info
            if "basic_info" in extracted_data:
                student_profile_data["basic_info"] = extracted_data["basic_info"]

            # Extract education summary
            if "education" in extracted_data:
                student_profile_data["education"] = extracted_data["education"]

            # Extract test_scores
            if "test_scores" in extracted_data:
                student_profile_data["test_scores"] = extracted_data["test_scores"]

            # Extract education_history and add to background if needed
            if "education_history" in extracted_data:
                education_history = extracted_data["education_history"]
                # Convert education_history to match EducationRecord schema
                # The education_history is already in the correct format from the prompt
                if "background" not in student_profile_data:
                    student_profile_data["background"] = {}
                student_profile_data["background"]["education_history"] = (
                    education_history
                )

            # 6. Extract highlights (already in correct format matching StudentHighlightCreateRequest)
            highlight_items = extracted_data.get("highlights", [])

            # Ensure all highlights have required fields with defaults
            for highlight in highlight_items:
                if "source_type" not in highlight:
                    highlight["source_type"] = "file_analysis"
                if "importance_score" not in highlight:
                    highlight["importance_score"] = 0.5
                if "tags" not in highlight:
                    highlight["tags"] = []

            logging.info(
                f"[Analysis Service] [Analyze Student File] Generated {len(highlight_items)} highlight items"
            )
            logging.info(
                f"[Analysis Service] [Analyze Student File] Extracted student profile data with keys: {list(student_profile_data.keys())}"
            )

            return parsed_text, student_profile_data, highlight_items

        except Exception as e:
            logging.error(
                f"[Analysis Service] [Analyze Student File] Error analyzing file {file_metadata.file_id}: {str(e)}"
            )
            logging.error(
                f"[Analysis Service] [Analyze Student File] Traceback: {traceback.format_exc()}"
            )
            raise

    async def get_agency_students_overview(
        self,
        agency_id: str,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get overview of students for an agency with pagination and filtering.

        Args:
            agency_id: The agency ID
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Dictionary of filters (student_name, student_id, target_degree, stage)

        Returns:
            Dictionary with total_count, total_pages, and students list
        """
        try:
            logging.info(
                f"[Analysis Service] [Get Agency Students Overview] Starting for agency_id: {agency_id}, skip: {skip}, limit: {limit}, filters: {filters}"
            )

            # Step 1: Get all member_ids for the agency
            member_ids = await self.agency_member_repo.find_member_ids_by_agency_id(
                agency_id
            )

            # Fallback: If no members found in agency_members, try to find students directly from student_assignments
            # This handles cases where student_assignments has data but agency_members doesn't
            if not member_ids:
                logging.info(
                    f"[Analysis Service] [Get Agency Students Overview] No members found in agency_members for agency_id: {agency_id}, trying fallback from student_assignments"
                )

                # Try to find students where member_id equals agency_id (fallback scenario)
                fallback_student_ids = (
                    await self.student_assignment_repo.find_student_ids_by_member_id(
                        agency_id
                    )
                )

                if fallback_student_ids:
                    logging.info(
                        f"[Analysis Service] [Get Agency Students Overview] Found {len(fallback_student_ids)} students using fallback method for agency_id: {agency_id}"
                    )
                    unique_student_ids = list(set(fallback_student_ids))
                else:
                    logging.info(
                        f"[Analysis Service] [Get Agency Students Overview] No students found for agency_id: {agency_id} (both primary and fallback methods)"
                    )
                    return {"total_count": 0, "total_pages": 0, "students": []}
            else:
                logging.info(
                    f"[Analysis Service] [Get Agency Students Overview] Found {len(member_ids)} members for agency_id: {agency_id}"
                )

                # Step 2: Get all student_ids assigned to these members
                all_student_ids = []
                for member_id in member_ids:
                    student_ids = await self.student_assignment_repo.find_student_ids_by_member_id(
                        member_id
                    )
                    all_student_ids.extend(student_ids)

                # Remove duplicates
                unique_student_ids = list(set(all_student_ids))

            if not unique_student_ids:
                logging.info(
                    f"[Analysis Service] [Get Agency Students Overview] No students found for agency_id: {agency_id}"
                )
                return {"total_count": 0, "total_pages": 0, "students": []}

            logging.info(
                f"[Analysis Service] [Get Agency Students Overview] Found {len(unique_student_ids)} unique students for agency_id: {agency_id}"
            )

            # Step 3: Build query with filters
            # Start with the base query: students must be in the agency's student list
            query = {"student_id": {"$in": unique_student_ids}}

            # Build filter conditions that need to be combined with $and
            filter_conditions = []

            if filters:
                # Apply student_name filter (search in first_name and last_name)
                if filters.get("student_name"):
                    student_name = filters["student_name"].strip()
                    if student_name:
                        search_pattern = {"$regex": student_name, "$options": "i"}
                        filter_conditions.append(
                            {
                                "$or": [
                                    {"basic_info.first_name": search_pattern},
                                    {"basic_info.last_name": search_pattern},
                                ]
                            }
                        )

                # Apply student_id filter - filter the student_ids list
                if filters.get("student_id"):
                    student_id_filter = filters["student_id"].strip()
                    if student_id_filter:
                        # Filter the student_ids list to only include matching ones
                        filtered_student_ids = [
                            sid
                            for sid in unique_student_ids
                            if student_id_filter.lower() in sid.lower()
                        ]
                        if filtered_student_ids:
                            query["student_id"] = {"$in": filtered_student_ids}
                        else:
                            # No matching student_ids, return empty result
                            logging.info(
                                f"[Analysis Service] [Get Agency Students Overview] No students match student_id filter: {student_id_filter}"
                            )
                            return {"total_count": 0, "total_pages": 0, "students": []}

                # Apply stage filter
                if filters.get("stage"):
                    stage = filters["stage"].strip()
                    if stage:
                        filter_conditions.append({"stage": stage})

                # Apply target_degree filter
                # Check if target_degree exists in education.target_degree or background.target_degree
                if filters.get("target_degree"):
                    target_degree = filters["target_degree"].strip()
                    if target_degree:
                        # Search in education.target_degree field
                        filter_conditions.append(
                            {
                                "$or": [
                                    {
                                        "education.target_degree": {
                                            "$regex": target_degree,
                                            "$options": "i",
                                        }
                                    },
                                    {
                                        "background.target_degree": {
                                            "$regex": target_degree,
                                            "$options": "i",
                                        }
                                    },
                                ]
                            }
                        )

            # Combine all filter conditions with $and if needed
            # The base query already has student_id filter, so we need to combine with $and
            if filter_conditions:
                if len(filter_conditions) == 1:
                    # If only one condition, we can merge it directly
                    # But we need to be careful with $or conditions
                    condition = filter_conditions[0]
                    if "$or" in condition:
                        # For $or conditions, we need to use $and to combine with base query
                        query["$and"] = filter_conditions
                    else:
                        # For simple conditions, merge directly
                        query.update(condition)
                else:
                    # Multiple conditions need $and
                    query["$and"] = filter_conditions

            # Step 4: Get paginated students using student_repo
            # Convert skip/limit to page/page_size
            page = (skip // limit) + 1 if limit > 0 else 1
            page_size = limit

            students, total_count = await self.student_repo.find_students_with_query(
                query=query, page=page, page_size=page_size, sort=[("created_at", -1)]
            )

            # Calculate total pages
            total_pages = math.ceil(total_count / limit) if limit > 0 else 0

            logging.info(
                f"[Analysis Service] [Get Agency Students Overview] Returning {len(students)}/{total_count} students for agency_id: {agency_id}"
            )

            return {
                "total_count": total_count,
                "total_pages": total_pages,
                "students": students,
            }

        except Exception as e:
            logging.error(
                f"[Analysis Service] [Get Agency Students Overview] Error: {str(e)}"
            )
            logging.error(
                f"[Analysis Service] [Get Agency Students Overview] Traceback: {traceback.format_exc()}"
            )
            raise
