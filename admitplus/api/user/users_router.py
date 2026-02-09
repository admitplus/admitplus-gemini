import logging
import traceback

from fastapi import APIRouter, HTTPException, Depends, Body

from .user_schema import (
    UserProfile,
    UserUpdateRequest,
    PasswordUpdateRequest,
    PasswordUpdateResponse,
    UserSettings,
    UserSettingsUpdateRequest,
    SecurityInfo,
)
from .invite_schema import (
    AcceptInviteRequest,
    AcceptInviteResponse,
)
from admitplus.common.response_schema import Response
from .user_service import UserService
from .invite_service import InviteService
from admitplus.dependencies.role_check import get_current_user


user_service = UserService()
invite_service = InviteService()


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=Response[UserProfile])
async def get_user_profile_handler(current_user: dict = Depends(get_current_user)):
    """
    Get current users's profile information
    """
    logging.info(
        f"[User Router] [Get Profile] Received profile request for users: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        result = await user_service.get_user_profile(current_user["user_id"])
        logging.info(
            f"[User Router] [Get Profile] Profile retrieved successfully for users: {current_user.get('user_id', 'Unknown')}"
        )

        return Response(
            code=200, message="User information retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Get Profile] Error retrieving profile for users {current_user.get('user_id', 'Unknown')}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Get Profile] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me", response_model=Response[UserProfile])
async def update_user_profile_handler(
    request: UserUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update users's profile information
    """
    logging.info(
        f"[User Router] [Update Profile] Received profile update request for users: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        result = await user_service.update_user_profile(
            current_user["user_id"], request
        )
        logging.info(
            f"[User Router] [Update Profile] Profile updated successfully for users: {current_user.get('user_id', 'Unknown')}"
        )

        return Response(
            code=200, message="User profile updated successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Update Profile] Error updating profile for users {current_user.get('user_id', 'Unknown')}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Update Profile] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/me/password", response_model=Response[PasswordUpdateResponse])
async def update_user_password_handler(
    request: PasswordUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update users's password
    """
    logging.info(
        f"[User Router] [Update Password] Received password update request for users: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        result = await user_service.update_user_password(
            current_user["user_id"], request
        )
        logging.info(
            f"[User Router] [Update Password] Password updated successfully for users: {current_user.get('user_id', 'Unknown')}"
        )

        return Response(code=200, message="Password updated successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Update Password] Error updating password for users {current_user.get('user_id', 'Unknown')}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Update Password] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/invites/accept", response_model=Response[AcceptInviteResponse])
async def accept_invite_handler(
    request: AcceptInviteRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept an invitation to join an agencies or organization
    """
    logging.info(
        f"[User Router] [Accept Invite] Received invite acceptance request from users: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        # Set user_id from current users if not provided
        if not request.user_id:
            request.user_id = current_user["user_id"]

        result = await invite_service.accept_invite(request)
        logging.info(
            f"[User Router] [Accept Invite] Invite accepted successfully for users: {current_user.get('user_id', 'Unknown')}"
        )

        return Response(code=200, message="Invite accepted successfully", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Accept Invite] Error accepting invite for users {current_user.get('user_id', 'Unknown')}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Accept Invite] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/settings", response_model=Response[UserSettings])
async def get_user_settings_handler(current_user: dict = Depends(get_current_user)):
    """
    Get current users's account settings
    """
    logging.info(
        f"[User Router] [Get Settings] Received settings request for users: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        result = await user_service.get_user_settings(current_user["user_id"])
        logging.info(
            f"[User Router] [Get Settings] Settings retrieved successfully for users: {current_user.get('user_id', 'Unknown')}"
        )

        return Response(
            code=200, message="User settings retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Get Settings] Error retrieving settings for users {current_user.get('user_id', 'Unknown')}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Get Settings] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/me/settings", response_model=Response[UserSettings])
async def update_user_settings_handler(
    request: UserSettingsUpdateRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Update current users's account settings
    """
    logging.info(
        f"[User Router] [Update Settings] Received settings update request for users: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        result = await user_service.update_user_settings(
            current_user["user_id"], request
        )
        logging.info(
            f"[User Router] [Update Settings] Settings updated successfully for users: {current_user.get('user_id', 'Unknown')}"
        )

        return Response(
            code=200, message="User settings updated successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Update Settings] Error updating settings for users {current_user.get('user_id', 'Unknown')}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Update Settings] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me/security", response_model=Response[SecurityInfo])
async def get_user_security_handler(current_user: dict = Depends(get_current_user)):
    """
    Get current users's security information
    """
    logging.info(
        f"[User Router] [Get Security] Received security info request for users: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        result = await user_service.get_user_security_info(current_user["user_id"])
        logging.info(
            f"[User Router] [Get Security] Security info retrieved successfully for users: {current_user.get('user_id', 'Unknown')}"
        )

        return Response(
            code=200, message="Security information retrieved successfully", data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Get Security] Error retrieving security info for users {current_user.get('user_id', 'Unknown')}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Get Security] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user-id-by-email", response_model=Response[dict])
async def get_user_id_by_email_handler(
    email: str, current_user: dict = Depends(get_current_user)
):
    """
    Get user_id by email address
    """
    logging.info(
        f"[User Router] [Get User ID By Email] Received request for email: {email} from user: {current_user.get('user_id', 'Unknown')}"
    )
    try:
        result = await user_service.get_user_id_by_email(email)

        if result:
            logging.info(
                f"[User Router] [Get User ID By Email] User ID found for email: {email}"
            )

            return Response(
                code=200,
                message="User ID retrieved successfully",
                data={"user_id": result, "email": email},
            )
        else:
            logging.warning(
                f"[User Router] [Get User ID By Email] User not found for email: {email}"
            )
            raise HTTPException(
                status_code=404, detail=f"User not found with email: {email}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(
            f"[User Router] [Get User ID By Email] Error retrieving user ID for email {email}: {str(e)}"
        )
        logging.error(
            f"[User Router] [Get User ID By Email] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
