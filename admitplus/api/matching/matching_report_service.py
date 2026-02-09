import json
import logging
import traceback
from bson import ObjectId
from datetime import datetime
from typing import List, Any

from admitplus.llm.prompts.gpt_prompts.matching_prompt.matching_report_prompt import (
    build_matching_report_prompt,
)
from admitplus.llm.prompts.gpt_prompts.matching_prompt.matching_insight_prompt import (
    build_matching_report_prompt as build_matching_insight_prompt,
)
from admitplus.llm.providers.openai.openai_client import generate_text
from admitplus.api.student.repos.student_profile_repo import StudentRepo
from admitplus.api.matching.matching_report_repo import MatchingReportRepo
from admitplus.api.universities.university_repo import UniversityRepo
from .matching_schema import (
    MatchingResult,
    ScoreBreakdown,
    RequirementsSnapshot,
    NextRound,
    ApplicationFee,
)


class MatchingReportService:
    def __init__(self):
        self.matching_report_repo = MatchingReportRepo()
        self.student_repo = StudentRepo()
        self.university_repo = UniversityRepo()
        logging.info("[Matching Report Service] Initialized with repositories")

    def _extract_study_level_from_student(self, student_info: dict) -> str:
        """
        Extract study_level from student_info based on student's stage.
        Maps StudentStage to study_level for querying admission cycles and requirements.
        """
        stage = student_info.get("stage", "unknown")

        # Map StudentStage to study_level
        stage_to_study_level = {
            "high_school": "undergraduate",  # High school students typically apply for undergraduate
            "undergraduate": "graduate",  # Undergraduate students typically apply for graduate
            "graduate": "phd",  # Graduate students typically apply for PhD
            "phd": "phd",  # PhD students might apply for another PhD
            "unknown": "graduate",  # Default to graduate if unknown
        }

        study_level = stage_to_study_level.get(stage, "graduate")
        logging.info(
            f"[Matching Report Service] Extracted study_level '{study_level}' from student stage '{stage}'"
        )
        return study_level

    def _clean_data_for_json(self, data):
        """Recursively clean data to ensure JSON serialization"""
        if isinstance(data, dict):
            return {k: self._clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data_for_json(item) for item in data]
        elif isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    def _transform_llm_response_to_matching_results(
        self, llm_response: Any
    ) -> List[MatchingResult]:
        """
        Transform LLM JSON response to List[MatchingResult]
        Handle various possible LLM output formats
        """
        try:
            logging.info(
                f"[Matching Report Service] [Transform] Starting transformation, input type: {type(llm_response)}"
            )

            # Parse if LLM returns a string
            if isinstance(llm_response, str):
                logging.info(
                    f"[Matching Report Service] [Transform] Parsing string response"
                )
                llm_response = json.loads(llm_response)
                logging.info(
                    f"[Matching Report Service] [Transform] Parsed to type: {type(llm_response)}"
                )

            # If LLM returns a dict, try to extract list
            if isinstance(llm_response, dict):
                logging.info(
                    f"[Matching Report Service] [Transform] Processing dict, keys: {list(llm_response.keys())}"
                )
                # Try common key names
                if "matching_results" in llm_response:
                    results = llm_response["matching_results"]
                    logging.info(
                        f"[Matching Report Service] [Transform] Found 'matching_results' key"
                    )
                elif "results" in llm_response:
                    results = llm_response["results"]
                    logging.info(
                        f"[Matching Report Service] [Transform] Found 'results' key"
                    )
                elif "data" in llm_response:
                    results = llm_response["data"]
                    logging.info(
                        f"[Matching Report Service] [Transform] Found 'data' key"
                    )
                elif isinstance(llm_response.get("matching_report"), list):
                    results = llm_response["matching_report"]
                    logging.info(
                        f"[Matching Report Service] [Transform] Found 'matching_report' key with list"
                    )
                elif "universities" in llm_response and isinstance(
                    llm_response["universities"], list
                ):
                    results = llm_response["universities"]
                    logging.info(
                        f"[Matching Report Service] [Transform] Found 'universities' key with list"
                    )
                else:
                    # If the entire dict is a result, convert to list
                    logging.info(
                        f"[Matching Report Service] [Transform] Treating entire dict as single result"
                    )
                    results = [llm_response]
            elif isinstance(llm_response, list):
                logging.info(
                    f"[Matching Report Service] [Transform] Processing list directly, length: {len(llm_response)}"
                )
                results = llm_response
            else:
                logging.error(
                    f"[Matching Report Service] [Transform] Unexpected LLM response type: {type(llm_response)}"
                )
                logging.error(
                    f"[Matching Report Service] [Transform] Response value: {str(llm_response)[:500]}"
                )
                return []

            logging.info(
                f"[Matching Report Service] [Transform] Extracted results list, length: {len(results) if isinstance(results, list) else 'N/A'}"
            )

            if not isinstance(results, list):
                logging.error(
                    f"[Matching Report Service] [Transform] Results is not a list, type: {type(results)}"
                )
                logging.error(
                    f"[Matching Report Service] [Transform] Results value: {str(results)[:500]}"
                )
                return []

            matching_results = []
            for idx, item in enumerate(results):
                try:
                    logging.info(
                        f"[Matching Report Service] [Transform] Processing item {idx + 1}/{len(results)}"
                    )
                    if not isinstance(item, dict):
                        logging.warning(
                            f"[Matching Report Service] [Transform] Item {idx} is not a dict, type: {type(item)}, skipping"
                        )
                        continue

                    logging.info(
                        f"[Matching Report Service] [Transform] Item {idx} keys: {list(item.keys())}"
                    )

                    # Extract or construct fields
                    score_breakdown_data = item.get("score_breakdown", {})
                    if not isinstance(score_breakdown_data, dict):
                        logging.warning(
                            f"[Matching Report Service] [Transform] Item {idx} score_breakdown is not a dict, using empty dict"
                        )
                        score_breakdown_data = {}

                    score_breakdown = ScoreBreakdown(
                        gpa=float(score_breakdown_data.get("gpa", 0)),
                        english=float(score_breakdown_data.get("english", 0)),
                        standardized=float(score_breakdown_data.get("standardized", 0)),
                        curriculum_alignment=float(
                            score_breakdown_data.get("curriculum_alignment", 0)
                        ),
                        research_internship=float(
                            score_breakdown_data.get("research_internship", 0)
                        ),
                        ranking_fit=float(score_breakdown_data.get("ranking_fit", 0)),
                        program_constraints=float(
                            score_breakdown_data.get("program_constraints", 0)
                        ),
                    )

                    requirements_data = item.get("requirements_snapshot", {})
                    if not isinstance(requirements_data, dict):
                        logging.warning(
                            f"[Matching Report Service] [Transform] Item {idx} requirements_snapshot is not a dict, using empty dict"
                        )
                        requirements_data = {}

                    requirements_snapshot = RequirementsSnapshot(
                        gpa_average=float(requirements_data.get("gpa_average", 0)),
                        toefl_min=float(requirements_data.get("toefl_min", 0)),
                        ielts_min=float(requirements_data.get("ielts_min", 0)),
                        sat_average=float(requirements_data.get("sat_average", 0)),
                        act_average=float(requirements_data.get("act_average", 0)),
                        gre_average=float(requirements_data.get("gre_average", 0)),
                    )

                    next_round_data = item.get("next_round", {})
                    if not isinstance(next_round_data, dict):
                        logging.warning(
                            f"[Matching Report Service] [Transform] Item {idx} next_round is not a dict, using defaults"
                        )
                        next_round_data = {}

                    next_round = NextRound(
                        name=next_round_data.get("name", "Unknown"),
                        deadline_date=next_round_data.get(
                            "deadline_date", "2025-12-31"
                        ),
                    )

                    application_fee_data = item.get("application_fee", {})
                    if not isinstance(application_fee_data, dict):
                        logging.warning(
                            f"[Matching Report Service] [Transform] Item {idx} application_fee is not a dict, using defaults"
                        )
                        application_fee_data = {}

                    application_fee = ApplicationFee(
                        amount=float(application_fee_data.get("amount", 0)),
                        currency=application_fee_data.get("currency", "USD"),
                    )

                    # Ensure lists are actually lists
                    top_positive_factors = item.get("top_positive_factors", [])
                    if not isinstance(top_positive_factors, list):
                        top_positive_factors = []

                    requirement_gaps = item.get("requirement_gaps", [])
                    if not isinstance(requirement_gaps, list):
                        requirement_gaps = []

                    action_recommendations = item.get("action_recommendations", [])
                    if not isinstance(action_recommendations, list):
                        action_recommendations = []

                    matching_result = MatchingResult(
                        university_id=item.get("university_id", ""),
                        university_name=item.get(
                            "university_name", "Unknown University"
                        ),
                        study_level=item.get(
                            "study_level", item.get("degree_level", "Graduate")
                        ),
                        overall_match=float(item.get("overall_match", 0)),
                        bucket=item.get("bucket", "Match"),
                        score_breakdown=score_breakdown,
                        matching_reason=item.get("matching_reason", ""),
                        risk_alert=item.get("risk_alert", ""),
                        top_positive_factors=top_positive_factors,
                        requirement_gaps=requirement_gaps,
                        action_recommendations=action_recommendations,
                        course_overlap_percent=float(
                            item.get("course_overlap_percent", 0)
                        ),
                        requirements_snapshot=requirements_snapshot,
                        next_round=next_round,
                        application_fee=application_fee,
                        notes=item.get("notes", ""),
                    )
                    matching_results.append(matching_result)
                    logging.info(
                        f"[Matching Report Service] [Transform] Successfully transformed item {idx + 1}"
                    )
                except Exception as e:
                    logging.error(
                        f"[Matching Report Service] [Transform] Error transforming item {idx}: {str(e)}"
                    )
                    logging.error(
                        f"[Matching Report Service] [Transform] Stack trace: {traceback.format_exc()}"
                    )
                    logging.error(
                        f"[Matching Report Service] [Transform] Item data: {json.dumps(item, indent=2, default=str)[:1000]}"
                    )
                    continue

            logging.info(
                f"[Matching Report Service] Successfully transformed {len(matching_results)} matching results"
            )
            return matching_results

        except Exception as e:
            logging.error(
                f"[Matching Report Service] Error transforming LLM response: {str(e)}"
            )
            logging.error(
                f"[Matching Report Service] Stack trace: {traceback.format_exc()}"
            )
            logging.error(f"[Matching Report Service] LLM response: {llm_response}")
            raise ValueError(
                f"Failed to transform LLM response to MatchingResult list: {str(e)}"
            )

    async def generate_matching_report(self, student_id, university_ids):
        try:
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Starting generation for student_id: {student_id}, university_ids: {university_ids}"
            )

            # Fetch student information
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Fetching student information for student_id: {student_id}"
            )
            student_info = await self.student_repo.find_student_by_id(student_id)

            if not student_info:
                logging.warning(
                    f"[Matching Report Service] [Generate Matching Report] Student not found: {student_id}"
                )
                raise ValueError(f"Student with ID '{student_id}' not found")

            # Clean ObjectId from student data
            student_info = self._clean_data_for_json(student_info)
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Successfully fetched and cleaned student information for student_id: {student_id}"
            )

            # Extract study_level from student_info
            study_level = self._extract_study_level_from_student(student_info)

            # Fetch universities information
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Fetching universities information for {len(university_ids)} universities"
            )
            university_info_list = []

            for university_id in university_ids:
                try:
                    logging.info(
                        f"[Matching Report Service] [Generate Matching Report] Fetching data for university_id: {university_id}"
                    )

                    university_profile = (
                        await self.university_repo.find_university_profile(
                            university_id
                        )
                    )

                    if not university_profile:
                        logging.warning(
                            f"[Matching Report Service] [Generate Matching Report] University profile not found for university_id: {university_id}, skipping"
                        )
                        continue

                    # Since no program_id is provided, we'll try to find a sample program for this university
                    # This helps provide more context to the LLM for generating matching reports
                    program_profile = None
                    try:
                        programs = (
                            await self.university_repo.find_programs_by_university_id(
                                university_id, limit=1
                            )
                        )
                        if programs and len(programs) > 0:
                            program_profile = programs[0]
                            logging.info(
                                f"[Matching Report Service] [Generate Matching Report] Found sample program for university_id: {university_id}"
                            )
                        else:
                            logging.warning(
                                f"[Matching Report Service] [Generate Matching Report] No programs found for university_id: {university_id}, continuing without program_profile"
                            )
                    except Exception as e:
                        logging.warning(
                            f"[Matching Report Service] [Generate Matching Report] Error fetching programs for university_id {university_id}: {str(e)}, continuing without program_profile"
                        )

                    # Fetch admission cycle and requirements using extracted study_level
                    admission_cycle = await self.university_repo.find_admission_cycle(
                        university_id, study_level
                    )
                    admission_requirements = (
                        await self.university_repo.find_admission_requirements(
                            university_id, study_level
                        )
                    )

                    university_info = {
                        "university_profile": university_profile,
                        "program_profile": program_profile,
                        "admission_cycle": admission_cycle,
                        "admission_requirements": admission_requirements,
                    }

                    # Clean ObjectId from universities data
                    university_info = self._clean_data_for_json(university_info)
                    university_info_list.append(university_info)

                    logging.info(
                        f"[Matching Report Service] [Generate Matching Report] Successfully fetched and cleaned data for university_id: {university_id}"
                    )
                except Exception as e:
                    logging.error(
                        f"[Matching Report Service] [Generate Matching Report] Error fetching data for university_id {university_id}: {str(e)}"
                    )
                    raise

            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Successfully fetched information for {len(university_info_list)} universities"
            )

            # Build prompt
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Building matching reports prompt"
            )
            matching_report_prompt = build_matching_report_prompt(
                student_info, university_info_list
            )
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Prompt built successfully"
            )

            # Generate reports using OpenAI
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Calling OpenAI to generate matching reports"
            )
            matching_report_response = await generate_text(matching_report_prompt)
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Successfully generated matching reports from OpenAI"
            )

            # Parse LLM JSON response
            try:
                logging.info(
                    f"[Matching Report Service] [Generate Matching Report] LLM response type: {type(matching_report_response)}"
                )
                logging.info(
                    f"[Matching Report Service] [Generate Matching Report] LLM response length: {len(str(matching_report_response))} characters"
                )

                if isinstance(matching_report_response, str):
                    # Try to extract JSON from markdown code blocks if present
                    response_str = matching_report_response.strip()
                    if response_str.startswith("```json"):
                        response_str = response_str[7:]
                    if response_str.startswith("```"):
                        response_str = response_str[3:]
                    if response_str.endswith("```"):
                        response_str = response_str[:-3]
                    response_str = response_str.strip()

                    matching_report = json.loads(response_str)
                else:
                    # If already an object, use directly
                    matching_report = matching_report_response

                logging.info(
                    f"[Matching Report Service] [Generate Matching Report] Successfully parsed matching reports: {type(matching_report)}"
                )
                logging.info(
                    f"[Matching Report Service] [Generate Matching Report] Parsed data structure: {type(matching_report).__name__}"
                )
                if isinstance(matching_report, dict):
                    logging.info(
                        f"[Matching Report Service] [Generate Matching Report] Dict keys: {list(matching_report.keys())}"
                    )
                elif isinstance(matching_report, list):
                    logging.info(
                        f"[Matching Report Service] [Generate Matching Report] List length: {len(matching_report)}"
                    )
            except json.JSONDecodeError as e:
                logging.error(
                    f"[Matching Report Service] [Generate Matching Report] Failed to parse LLM response as JSON: {e}"
                )
                logging.error(
                    f"[Matching Report Service] [Generate Matching Report] Raw response (first 500 chars): {str(matching_report_response)[:500]}"
                )
                raise ValueError("Failed to parse LLM response as JSON")

            # Insert reports into database
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Inserting matching reports into database for student_id: {student_id}"
            )
            insert_id = self.matching_report_repo.insert_matching_report(
                student_id, matching_report
            )

            if insert_id:
                logging.info(
                    f"[Matching Report Service] [Generate Matching Report] Successfully inserted matching reports with id: {insert_id} for student_id: {student_id}"
                )
            else:
                logging.error(
                    f"[Matching Report Service] [Generate Matching Report] Failed to insert matching reports for student_id: {student_id}"
                )

            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Successfully completed generation for student_id: {student_id}"
            )

            # Transform LLM output to List[MatchingResult]
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Transforming LLM response to MatchingResult list"
            )
            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Input data type: {type(matching_report)}"
            )
            if isinstance(matching_report, dict):
                logging.info(
                    f"[Matching Report Service] [Generate Matching Report] Input dict keys: {list(matching_report.keys())}"
                )
            elif isinstance(matching_report, list):
                logging.info(
                    f"[Matching Report Service] [Generate Matching Report] Input list length: {len(matching_report)}"
                )

            matching_results = self._transform_llm_response_to_matching_results(
                matching_report
            )

            logging.info(
                f"[Matching Report Service] [Generate Matching Report] Transformed {len(matching_results)} matching results"
            )
            if len(matching_results) == 0:
                logging.warning(
                    f"[Matching Report Service] [Generate Matching Report] WARNING: No matching results were generated!"
                )
                logging.warning(
                    f"[Matching Report Service] [Generate Matching Report] Original LLM response structure: {type(matching_report)}"
                )
                if isinstance(matching_report, dict):
                    logging.warning(
                        f"[Matching Report Service] [Generate Matching Report] Dict content: {json.dumps(matching_report, indent=2, default=str)[:1000]}"
                    )
                elif isinstance(matching_report, list):
                    logging.warning(
                        f"[Matching Report Service] [Generate Matching Report] List content: {json.dumps(matching_report, indent=2, default=str)[:1000]}"
                    )

            # Return transformed list
            return matching_results

        except Exception as e:
            logging.error(
                f"[Matching Report Service] [Generate Matching Report] Error generating matching reports for student_id {student_id}: {str(e)}"
            )
            raise

    async def generate_university_match_insight(
        self, student_id: str, university_id: str, program_id: str
    ):
        try:
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Starting for student_id: {student_id}, university_id: {university_id}, program_id: {program_id}"
            )

            # Fetch student information
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Fetching student information for student_id: {student_id}"
            )
            student_info = await self.student_repo.find_student_by_id(student_id)

            if not student_info:
                logging.warning(
                    f"[Matching Report Service] [Generate University Match Insight] Student not found: {student_id}"
                )
                raise ValueError(f"Student with ID '{student_id}' not found")

            # Fetch universities profile
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Fetching universities profile for university_id: {university_id}"
            )
            university_profile = await self.university_repo.find_university_profile(
                university_id
            )

            if not university_profile:
                logging.warning(
                    f"[Matching Report Service] [Generate University Match Insight] University profile not found: {university_id}"
                )
                raise ValueError(
                    f"University profile with ID '{university_id}' not found"
                )

            # Fetch program profile
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Fetching program profile for university_id: {university_id}, program_id: {program_id}"
            )
            program_profile = await self.university_repo.find_program_profile(
                university_id, program_id
            )

            if not program_profile:
                logging.warning(
                    f"[Matching Report Service] [Generate University Match Insight] Program profile not found: university_id={university_id}, program_id={program_id}"
                )
                raise ValueError(
                    f"Program profile with ID '{program_id}' not found for universities '{university_id}'"
                )

            # Extract study_level from program_profile or use a default
            study_level = (
                program_profile.get("study_level")
                or program_profile.get("degree_level")
                or ""
            )
            if not study_level:
                logging.warning(
                    f"[Matching Report Service] [Generate University Match Insight] study_level not found in program_profile, using empty string"
                )

            # Fetch admission cycle
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Fetching admission cycle for university_id: {university_id}, study_level: {study_level}"
            )
            admission_cycle = await self.university_repo.find_admission_cycle(
                university_id, study_level
            )

            # Fetch admission requirements by program_id
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Fetching admission requirements for program_id: {program_id}"
            )
            requirements = (
                await self.university_repo.find_admission_requirement_by_program_id(
                    program_id
                )
            )

            # Build prompt using the correct function
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Building matching insight prompt"
            )
            university_match_insight_prompt = build_matching_insight_prompt(
                student_info,
                university_profile,
                program_profile,
                admission_cycle,
                requirements,
            )

            # Generate insight using OpenAI
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Calling OpenAI to generate matching insight"
            )
            university_match_insight = await generate_text(
                university_match_insight_prompt
            )
            logging.info(
                f"[Matching Report Service] [Generate University Match Insight] Successfully generated matching insight"
            )

            return university_match_insight
        except ValueError:
            raise
        except Exception as e:
            logging.error(
                f"[Matching Report Service] [Generate University Match Insight] Error generating matching insight for student_id {student_id}, university_id {university_id}, program_id {program_id}: {str(e)}"
            )
            logging.error(
                f"[Matching Report Service] [Generate University Match Insight] Stack trace: {traceback.format_exc()}"
            )
            raise
