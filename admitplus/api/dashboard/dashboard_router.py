import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException

from admitplus.config import settings
from admitplus.dependencies.role_check import get_current_user
from admitplus.common.response_schema import Response
from admitplus.api.dashboard.dashboard_service import DashboardService

dashboard_service = DashboardService()

router = APIRouter(prefix="/dashboard/application", tags=["Dashboard"])


@router.get("/agency/{agency_id}")
async def get_agency_dashboard_handler(
    agency_id: str, current_user: dict = Depends(get_current_user)
):
    """Get agencies dashboard data"""
    try:
        logging.info(
            f"[Dashboard Router] [Agency Dashboard] Starting for agencies {agency_id}"
        )
        logging.info(
            f"[Dashboard Router] [Agency Dashboard] Requested by user: {current_user.get('user_id', 'Unknown')}"
        )

        # Check authorization
        user_role = current_user.get("role")
        if user_role not in [settings.USER_ROLE_AGENCY]:
            logging.warning(
                f"[Dashboard Router] [Agency Dashboard] Access denied for user {current_user.get('user_id')} with role {user_role}"
            )
            raise HTTPException(
                status_code=403, detail="Access denied. Insufficient permissions"
            )

        result = await dashboard_service.get_agency_dashboard(agency_id)

        logging.info(
            f"[Dashboard Router] [Agency Dashboard] Successfully retrieved dashboard for agencies: {agency_id}"
        )
        return Response(
            code=200, message="Agency dashboard retrieved successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Dashboard Router] [Agency Dashboard] Error: {str(e)}")
        logging.error(
            f"[Dashboard Router] [Agency Dashboard] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/teacher/{teacher_id}")
async def get_teacher_dashboard_handler(
    teacher_id: str, current_user: dict = Depends(get_current_user)
):
    """Get teachers dashboard data"""
    try:
        logging.info(
            f"[Dashboard Router] [Teacher Dashboard] Starting for teachers {teacher_id}"
        )
        logging.info(
            f"[Dashboard Router] [Teacher Dashboard] Requested by user: {current_user.get('user_id', 'Unknown')}"
        )

        # Check authorization
        user_role = current_user.get("role")
        if user_role not in [settings.USER_ROLE_TEACHER]:
            logging.warning(
                f"[Dashboard Router] [Teacher Dashboard] Access denied for user {current_user.get('user_id')} with role {user_role}"
            )
            raise HTTPException(
                status_code=403, detail="Access denied. Insufficient permissions"
            )

        result = await dashboard_service.get_teacher_dashboard(teacher_id)

        logging.info(
            f"[Dashboard Router] [Teacher Dashboard] Successfully retrieved dashboard for teachers: {teacher_id}"
        )
        return Response(
            code=200, message="Teacher dashboard retrieved successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Dashboard Router] [Teacher Dashboard] Error: {str(e)}")
        logging.error(
            f"[Dashboard Router] [Teacher Dashboard] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/student/{student_id}")
async def get_student_dashboard_handler(
    student_id: str, current_user: dict = Depends(get_current_user)
):
    """Get students dashboard data"""
    try:
        logging.info(
            f"[Dashboard Router] [Student Dashboard] Starting for students {student_id}"
        )
        logging.info(
            f"[Dashboard Router] [Student Dashboard] Requested by user: {current_user.get('user_id', 'Unknown')}"
        )

        # Check authorization
        user_role = current_user.get("role")
        if user_role not in [settings.USER_ROLE_STUDENT]:
            logging.warning(
                f"[Dashboard Router] [Student Dashboard] Access denied for user {current_user.get('user_id')} with role {user_role}"
            )
            raise HTTPException(
                status_code=403, detail="Access denied. Insufficient permissions"
            )

        result = await dashboard_service.get_student_dashboard(student_id)

        logging.info(
            f"[Dashboard Router] [Student Dashboard] Successfully retrieved dashboard for students: {student_id}"
        )
        return Response(
            code=200, message="Student dashboard retrieved successfully", data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[Dashboard Router] [Student Dashboard] Error: {str(e)}")
        logging.error(
            f"[Dashboard Router] [Student Dashboard] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
