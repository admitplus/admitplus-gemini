from fastapi import APIRouter

from .auth.auth_router import router as auth_router
from .agency.agencies_router import router as agency_router
from .agency.agency_members_router import router as agency_member_router
from .dashboard.dashboard_router import router as dashboard_router
from .essays.essay_router import router as essays_router
from .exams.exam_attempts_router import router as exam_router
from .exams.exam_evaluation_router import router as exam_feedback_router
from .exams.exam_tasks_router import router as exam_tasks_router
from .feedback.feedback_router import router as feedback_router
from .files.files_router import router as file_router
from .files.avatar_router import router as avatar_router
from .matching.matching_report_router import router as matching_report_router
from .matching.matching_router import router as matching_router
from .student.application.applications_router import (
    router as student_applications_router,
)
from .student.files.files_router import router as student_files_router
from .student.highlights.highlight_router import router as student_highlights_router
from .student.profile.agency_router import router as student_agency_router
from .surveys.surveys_router import router as surveys_router
from .universities.autocomplete_router import router as autocomplete_router
from .universities.university_router import router as universities_router
from .user.users_router import router as user_router
from .user.invite_router import router as invitation_router

invite_router = APIRouter(prefix="")
invite_router.include_router(invitation_router)

router = APIRouter(prefix="/api/v1")

for each_router in [
    auth_router,
    agency_router,
    agency_member_router,
    dashboard_router,
    essays_router,
    exam_router,
    exam_feedback_router,
    exam_tasks_router,
    feedback_router,
    file_router,
    avatar_router,
    matching_report_router,
    matching_router,
    student_applications_router,
    student_files_router,
    student_highlights_router,
    student_agency_router,
    surveys_router,
    autocomplete_router,
    universities_router,
    user_router,
]:
    router.include_router(each_router)
