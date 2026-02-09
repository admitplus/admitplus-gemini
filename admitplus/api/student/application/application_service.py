import logging
from datetime import datetime

from fastapi import HTTPException

from .application_repo import ApplicationRepo
from admitplus.api.universities.information_repo import InformationRepo
from ..schemas.application.application_schema import (
    StudentApplicationCreateRequest,
    StudentApplicationResponse,
    StudentApplicationListResponse,
    StudentApplicationDetailResponse,
    StudentApplicationUpdateRequest,
)
from admitplus.utils.crypto_utils import generate_uuid


class ApplicationService:
    def __init__(self):
        self.application_repo = ApplicationRepo()
        self.information_repo = InformationRepo()
        logging.info(f"[Application Service] Initialized")

    async def _get_university_logo(self, university_id: str) -> str:
        """
        Helper method to fetch university logo URL from university_id
        Supports both UUID format and university name strings
        Returns empty string if logo not found
        """
        try:
            if not university_id:
                return ""

            # First try to find by ID (works for UUID format)
            university_profile = await self.information_repo.find_university_by_id(
                university_id
            )

            # If not found by ID, try to find by name (for legacy data where university_id might be a name)
            if not university_profile:
                logging.debug(
                    f"[Application Service] [_GetUniversityLogo] Not found by ID, trying by name: {university_id}"
                )
                university_profile = (
                    await self.information_repo.find_university_by_name(university_id)
                )

            if not university_profile:
                logging.warning(
                    f"[Application Service] [_GetUniversityLogo] University profile not found for university_id={university_id}"
                )
                return ""

            # Try common logo field names
            university_logo = (
                university_profile.get("logo_url")
                or university_profile.get("logo")
                or ""
            )

            return university_logo if university_logo else ""
        except Exception as e:
            logging.warning(
                f"[Application Service] [_GetUniversityLogo] Failed to get university logo for university_id={university_id}: {e}"
            )
            return ""

    async def create_application(
        self, student_id: str, request: StudentApplicationCreateRequest, created_by: str
    ) -> StudentApplicationResponse:
        """
        Create a new application for a student
        """
        try:
            logging.info(
                f"[Application Service] [Create Application] Creating application for student {student_id}"
            )

            # Validate input
            if not student_id or not student_id.strip():
                raise HTTPException(status_code=400, detail="Student ID is required")

            if not request.university_name or not request.university_name.strip():
                raise HTTPException(
                    status_code=400, detail="University name is required"
                )

            if not request.program_name or not request.program_name.strip():
                raise HTTPException(status_code=400, detail="Program name is required")

            if not request.degree_level or not request.degree_level.strip():
                raise HTTPException(status_code=400, detail="Degree level is required")

            # Generate application ID
            application_id = generate_uuid()

            # Prepare application data
            application_data = {
                "application_id": application_id,
                "student_id": student_id,
                "university_id": request.university_id,
                "university_name": request.university_name.strip(),
                "program_name": request.program_name.strip(),
                "degree_level": request.degree_level.strip(),
                "status": "planning",
                "created_by_member_id": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Create application in database
            insert_id = await self.application_repo.create_application(application_data)
            if not insert_id:
                raise HTTPException(
                    status_code=500, detail="Failed to create application"
                )

            # Fetch university logo
            university_logo = await self._get_university_logo(request.university_id)

            # Return response
            return StudentApplicationResponse(
                application_id=application_id,
                student_id=student_id,
                university_id=request.university_id,
                university_name=request.university_name,
                university_logo=university_logo,
                program_name=request.program_name,
                degree_level=request.degree_level,
                status="draft",
                result=None,
                created_by_member_id=created_by,
                created_at=application_data["created_at"],
                updated_at=application_data["updated_at"],
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Service] [Create Application] Error creating application: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to create application")

    async def list_applications(
        self, student_id: str
    ) -> StudentApplicationListResponse:
        """
        Get applications by student id
        """
        try:
            logging.info(
                f"[Application Service] [List Applications] Getting applications for student {student_id}"
            )

            applications_data = (
                await self.application_repo.find_applications_by_student(student_id)
            )

            application_list = []
            for app_data in applications_data:
                university_id = app_data.get("university_id", "")
                university_logo = (
                    await self._get_university_logo(university_id)
                    if university_id
                    else ""
                )

                application_list.append(
                    StudentApplicationResponse(
                        application_id=app_data.get("application_id", ""),
                        student_id=app_data.get("student_id", student_id),
                        university_id=university_id,
                        university_name=app_data.get("university_name", ""),
                        university_logo=university_logo,
                        program_name=app_data.get("program_name", ""),
                        degree_level=app_data.get("degree_level", ""),
                        status=app_data.get("status", "planning"),
                        result=app_data.get("result"),
                        created_by_member_id=app_data.get("created_by_member_id"),
                        created_at=app_data.get("created_at"),
                        updated_at=app_data.get("updated_at"),
                    )
                )

            logging.info(
                f"[Application Service] [List Applications] Found {len(application_list)} applications for student {student_id}"
            )
            return StudentApplicationListResponse(application_list=application_list)

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Service] [List Applications] Error getting applications for student {student_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to get applications")

    async def get_application(
        self, application_id: str
    ) -> StudentApplicationDetailResponse:
        """
        Get application by ID
        """
        try:
            app_data = await self.application_repo.find_application_by_id(
                application_id
            )
            if not app_data:
                raise HTTPException(status_code=404, detail="Application not found")

            university_id = app_data.get("university_id", "")
            university_logo = (
                await self._get_university_logo(university_id) if university_id else ""
            )

            return StudentApplicationDetailResponse(
                application_id=app_data.get("application_id", ""),
                student_id=app_data.get("student_id", ""),
                university_id=university_id,
                university_name=app_data.get("university_name", ""),
                university_logo=university_logo,
                program_name=app_data.get("program_name", ""),
                degree_level=app_data.get("degree_level", ""),
                status=app_data.get("status", "planning"),
                result=app_data.get("result"),
                created_by_member_id=app_data.get("created_by_member_id"),
                created_at=app_data.get("created_at"),
                updated_at=app_data.get("updated_at"),
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Service] [Get Application] Error getting application {application_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to get application")

    async def update_application(
        self,
        application_id: str,
        request: StudentApplicationUpdateRequest,
        updated_by: str,
    ) -> StudentApplicationDetailResponse:
        """
        Update application
        """
        try:
            logging.info(
                f"[Application Service] [Update Application] Updating application {application_id}"
            )

            # Check if application exists
            existing_app = await self.application_repo.find_application_by_id(
                application_id
            )
            if not existing_app:
                raise HTTPException(status_code=404, detail="Application not found")

            # Convert request to dict, excluding None values
            update_data = request.model_dump(exclude_none=True)

            # Update application
            result = await self.application_repo.update_application(
                application_id, update_data
            )
            if not result:
                raise HTTPException(
                    status_code=500, detail="Failed to update application"
                )

            # Get updated application
            updated_app = await self.get_application(application_id)
            return updated_app

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Service] [Update Application] Error updating application {application_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to update application")

    async def delete_application(
        self, application_id: str, deleted_by: str
    ) -> StudentApplicationDetailResponse:
        """
        Soft delete application
        """
        try:
            logging.info(
                f"[Application Service] [Delete Application] Soft deleting application {application_id}"
            )

            # Check if application exists
            existing_app = await self.application_repo.find_application_by_id(
                application_id
            )

            if not existing_app:
                raise HTTPException(status_code=404, detail="Application not found")

            data = {"deleted_by": deleted_by, "status": "deleted"}

            result = await self.application_repo.delete_application(
                application_id, data
            )

            if not result:
                raise HTTPException(
                    status_code=500, detail="Failed to delete application"
                )

            # Get updated application
            updated_app = await self.get_application(application_id)

            return updated_app
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Application Service] [Delete Application] Error deleting application {application_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to delete application")
