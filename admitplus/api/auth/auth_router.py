import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Response

from admitplus.dependencies.role_check import get_current_user
from admitplus.common.exceptions import DuplicateEmailError
from admitplus.api.auth.auth_schema import (
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    SendCodeRequest,
    SignUpRequest,
    SignUpResponse,
    TokenResponse,
    VerifyEmailCodeRequest,
    SetPasswordRequest,
    MessageResponse,
)
from admitplus.common.response_schema import Response
from .token_schema import RefreshRequest
from .auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/sign-up", response_model=Response[SignUpResponse])
async def sign_up_handler(sign_up_data: SignUpRequest):
    """
    Register a new users account with email verification
    """
    logging.info(
        f"[Auth Router] [SignUp] Received sign-up request for email: {sign_up_data.email}"
    )
    try:
        result = await auth_service.sign_up(sign_up_data)
        logging.info(
            f"[Auth Router] [SignUp] User registered successfully: {sign_up_data.email}"
        )
        return Response(code=201, message="User registration completed", data=result)
    except DuplicateEmailError:
        logging.warning(
            f"[Auth Router] [SignUp] Duplicate email attempt: {sign_up_data.email}"
        )
        raise HTTPException(status_code=409, detail="Email already registered")
    except Exception as e:
        logging.error(
            f"[Auth Router] [SignUp] Error during sign-up for email {sign_up_data.email}: {str(e)}"
        )
        logging.error(f"[Auth Router] [SignUp] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error during agencies registration"
        )


@router.post("/login", response_model=Response[LoginResponse])
async def login_handler(request: LoginRequest):
    """
    Authenticate users and return access/refresh tokens
    """
    logging.info(f"[Auth Router] [Login] Login attempt for email: {request.email}")
    try:
        user = await auth_service.login(request)
        logging.info(
            f"[Auth Router] [Login] User logged in successfully: {request.email}"
        )
        return Response(code=200, message="Authentication successful", data=user)
    except HTTPException as http_err:
        logging.warning(
            f"[Auth Router] [Login] Failed login attempt for email {request.email}: {http_err.detail}"
        )
        raise http_err
    except Exception as e:
        logging.error(
            f"[Auth Router] [Login] Unexpected error during login for email {request.email}: {str(e)}"
        )
        logging.error(f"[Auth Router] [Login] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error during login"
        )


@router.post("/logout", response_model=Response[MessageResponse])
async def logout_handler(user=Depends(get_current_user)):
    """
    Logout users and invalidate their tokens
    """
    user_id = user["user_id"]  # 从JWT token中获取用户ID，确保安全性

    logging.info(
        f"[Auth Router] [Logout] Logout request received for user_id: {user_id}"
    )
    try:
        await auth_service.logout(user_id)
        logging.info(f"[Auth Router] [Logout] User logged out successfully: {user_id}")
        return Response(code=200, message="Logout completed")
    except HTTPException as e:
        logging.warning(
            f"[Auth Router] [Logout] Failed to logout users {user_id}: {e.detail}"
        )
        raise e
    except Exception as e:
        logging.error(
            f"[Auth Router] [Logout] Unexpected error during logout for users {user_id}: {str(e)}"
        )
        logging.error(f"[Auth Router] [Logout] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="Internal server error during logout"
        )


@router.post("/refresh-token", response_model=Response[TokenResponse])
async def refresh_token_handler(request: RefreshRequest):
    """
    Refresh access token using refresh token
    """
    logging.info("[Auth Router] [Refresh Token] Refresh token request received")
    try:
        new_tokens = await auth_service.refresh_token(request.refresh_token)
        logging.info("[Auth Router] [Refresh Token] Token refreshed successfully")
        return Response(code=200, message="Token refresh completed", data=new_tokens)
    except HTTPException as e:
        logging.warning(
            f"[Auth Router] [Refresh Token] Failed to refresh token: {e.detail}"
        )
        raise e
    except Exception as e:
        logging.error(
            f"[Auth Router] [Refresh Token] Error during token refresh: {str(e)}"
        )
        logging.error(
            f"[Auth Router] [Refresh Token] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during token refresh"
        )


@router.post("/reset-password", response_model=Response[MessageResponse])
async def reset_password_handler(request: ResetPasswordRequest):
    """
    Reset users password with verification code
    """
    logging.info(
        f"[Auth Router] [ResetPassword] Password reset request for email: {request.email}"
    )
    try:
        data = await auth_service.reset_password(
            request.email, request.password, request.code
        )
        logging.info(
            f"[Auth Router] [ResetPassword] Password reset successful for email: {request.email}"
        )
        return Response(code=200, message="Password reset completed", data=data)
    except HTTPException as e:
        logging.warning(
            f"[Auth Router] [ResetPassword] Password reset failed for email {request.email}: {e.detail}"
        )
        raise e
    except Exception as e:
        logging.error(
            f"[Auth Router] [ResetPassword] Error resetting password for email {request.email}: {str(e)}"
        )
        logging.error(
            f"[Auth Router] [ResetPassword] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during password reset"
        )


@router.post("/send-code", response_model=Response[MessageResponse])
async def send_verification_code_handler(request: SendCodeRequest):
    """
    Send verification code to users email for various purposes
    """
    logging.info(
        f"[Auth Router] [Send Verification Code] Send code request for email: {request.email}"
    )
    try:
        data = await auth_service.send_verification_code(request.email, request.purpose)
        logging.info(
            f"[Auth Router] [Send Verification Code] Verification code sent successfully to email: {request.email}"
        )
        return Response(code=200, message="Verification code sent", data=data)
    except HTTPException as e:
        logging.warning(
            f"[Auth Router] [Send Verification Code] Failed to send verification code: {e.detail}"
        )
        raise e
    except Exception as e:
        logging.error(
            f"[Auth Router] [Send Verification Code] Error sending code to {request.email}: {str(e)}"
        )
        logging.error(
            f"[Auth Router] [Send Verification Code] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during code sending"
        )


@router.post("/verify-code", response_model=Response[MessageResponse])
async def verify_email_code_handler(request: VerifyEmailCodeRequest):
    """
    Verify email verification code for various purposes
    """
    logging.info(
        f"[Auth Router] [Verify Email Code] Verification request for email: {request.email}"
    )
    try:
        data = await auth_service.verify_email_code(
            request.email, request.purpose, request.code
        )
        logging.info(
            f"[Auth Router] [Verify Email Code] Email verified successfully: {request.email}"
        )
        return Response(code=200, message="Email verification completed", data=data)
    except HTTPException as e:
        logging.warning(
            f"[Auth Router] [Verify Email Code] Failed to verify email code: {e.detail}"
        )
        raise e
    except Exception as e:
        logging.error(
            f"[Auth Router] [Verify Email Code] Error verifying email {request.email}: {str(e)}"
        )
        logging.error(
            f"[Auth Router] [Verify Email Code] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during email verification"
        )


@router.post("/set-password", response_model=Response[MessageResponse])
async def set_password_handler(request: SetPasswordRequest):
    """
    Set password after invitation acceptance
    """
    logging.info(
        f"[Auth Router] [SetPassword] Setting password for email: {request.email}"
    )
    try:
        data = await auth_service.set_password(request.email, request.password)
        logging.info(
            f"[Auth Router] [SetPassword] Password set successfully for email: {request.email}"
        )
        return Response(code=200, message="Password set successfully", data=data)
    except HTTPException as e:
        logging.warning(
            f"[Auth Router] [SetPassword] Password set failed for email {request.email}: {e.detail}"
        )
        raise e
    except Exception as e:
        logging.error(
            f"[Auth Router] [SetPassword] Error setting password for email {request.email}: {str(e)}"
        )
        logging.error(
            f"[Auth Router] [SetPassword] Stack trace: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during password setup"
        )
