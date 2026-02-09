from typing import Any, Dict

from admitplus.api.student.student_service import StudentService
from admitplus.api.student.schemas.student_schema import StudentUpdateRequest

student_service = StudentService()


async def get_user_profile_by_id(user_id: str) -> Dict[str, Any]:
    """
    Retrieve a user's profile by ID as an ADK function tool.

    Args:
        user_id (str): The unique identifier of the user (student ID).

    Returns:
        dict: A tool-friendly response with the following keys:

            - ``status`` (str): ``\"success\"`` if the profile was found,
              otherwise ``\"error\"``.
            - ``profile`` (dict | None): The student's profile data in
              dictionary form when successful, otherwise ``None``.
            - ``error_message`` (str | None): A human-readable explanation when
              ``status`` is ``\"error\"``, otherwise ``None``.
    """
    try:
        profile = await student_service.get_student_detail(user_id)
        if hasattr(profile, "model_dump"):
            profile_dict = profile.model_dump(mode="json", exclude_none=True)
        else:
            profile_dict = profile

        return {
            "status": "success",
            "profile": profile_dict,
            "error_message": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "profile": None,
            "error_message": str(exc),
        }


async def update_user_profile_by_id(
    user_id: str, profile_update: StudentUpdateRequest
) -> Dict[str, Any]:
    """
    Update a user's profile by ID as an ADK function tool.

    Args:
        user_id (str): The unique identifier of the user (student ID).
        profile_update (StudentUpdateRequest): The profile fields to update.
            Only non-null fields are applied; nested ``basic_info`` fields are
            merged with existing data.

    Returns:
        dict: A tool-friendly response with the following keys:

            - ``status`` (str): ``\"success\"`` if the update completed,
              otherwise ``\"error\"``.
            - ``updated_profile`` (dict | None): The updated student's profile
              as a dictionary when successful, otherwise ``None``.
            - ``error_message`` (str | None): A human-readable explanation when
              ``status`` is ``\"error\"``, otherwise ``None``.
    """
    try:
        updated_profile = await student_service.update_student_profile(
            user_id, profile_update
        )
        if hasattr(updated_profile, "model_dump"):
            updated_profile_dict = updated_profile.model_dump(
                mode="json", exclude_none=True
            )
        else:
            updated_profile_dict = updated_profile

        return {
            "status": "success",
            "updated_profile": updated_profile_dict,
            "error_message": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "error",
            "updated_profile": None,
            "error_message": str(exc),
        }
