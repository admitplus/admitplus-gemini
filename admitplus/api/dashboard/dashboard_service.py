import logging
from typing import Dict, Any

from admitplus.api.agency.agency_profile_repo import AgencyRepo
from admitplus.api.student.student_service import StudentService


class DashboardService:
    def __init__(self):
        self.agency_repo = AgencyRepo()
        self.student_service = StudentService()

    async def get_agency_dashboard(self, agency_id: str) -> Dict[str, Any]:
        try:
            logging.info(
                f"[Dashboard Service] [Agency Dashboard] Starting for agencies {agency_id}"
            )

            # Get agencies basic info
            agency_info = await self.agency_repo.find_agency_by_id(agency_id)
            if not agency_info:
                logging.warning(
                    f"[Dashboard Service] [Agency Dashboard] Agency not found: {agency_id}"
                )
                return {"error": "Agency not found"}

            # Get students statistics
            student_info = await self.student_service.list_agency_students(agency_id)

            dashboard_data = {
                "agency_id": agency_id,
                "agency_name": agency_info.get("name", ""),
                "total_students": len(student_info) if student_info else 0,
                "students": student_info,
                "metrics": {
                    "active_students": len(
                        [s for s in (student_info or []) if s.get("status") == "active"]
                    ),
                    "pending_students": len(
                        [
                            s
                            for s in (student_info or [])
                            if s.get("status") == "pending"
                        ]
                    ),
                },
            }

            logging.info(
                f"[Dashboard Service] [Agency Dashboard] Successfully retrieved dashboard for agencies: {agency_id}"
            )
            return dashboard_data

        except Exception as e:
            logging.error(f"[Dashboard Service] [Agency Dashboard] Error: {str(e)}")
            return {"error": "Failed to retrieve agencies dashboard"}

    async def get_teacher_dashboard(self, teacher_id: str) -> Dict[str, Any]:
        try:
            logging.info(
                f"[Dashboard Service] [Teacher Dashboard] Starting for teachers {teacher_id}"
            )

            # Get teachers's assigned students
            student_info = await self.student_service.list_agency_students(teacher_id)

            dashboard_data = {
                "teacher_id": teacher_id,
                "total_students": len(student_info) if student_info else 0,
                "students": student_info,
                "metrics": {
                    "active_students": len(
                        [s for s in (student_info or []) if s.get("status") == "active"]
                    ),
                    "pending_students": len(
                        [
                            s
                            for s in (student_info or [])
                            if s.get("status") == "pending"
                        ]
                    ),
                },
            }

            logging.info(
                f"[Dashboard Service] [Teacher Dashboard] Successfully retrieved dashboard for teachers: {teacher_id}"
            )
            return dashboard_data

        except Exception as e:
            logging.error(f"[Dashboard Service] [Teacher Dashboard] Error: {str(e)}")
            return {"error": "Failed to retrieve teachers dashboard"}

    async def get_student_dashboard(self, student_id: str) -> Dict[str, Any]:
        try:
            logging.info(
                f"[Dashboard Service] [Student Dashboard] Starting for students {student_id}"
            )

            # Get students information and progress
            student_info = await self.student_service.list_agency_students(student_id)

            dashboard_data = {
                "student_id": student_id,
                "student_info": student_info[0] if student_info else {},
                "progress": {
                    "completed_assignments": 0,  # Placeholder
                    "pending_assignments": 0,  # Placeholder
                    "overall_progress": 0,  # Placeholder
                },
            }

            logging.info(
                f"[Dashboard Service] [Student Dashboard] Successfully retrieved dashboard for students: {student_id}"
            )
            return dashboard_data

        except Exception as e:
            logging.error(f"[Dashboard Service] [Student Dashboard] Error: {str(e)}")
            return {"error": "Failed to retrieve students dashboard"}
