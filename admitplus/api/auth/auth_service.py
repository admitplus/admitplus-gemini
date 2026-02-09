import json
import logging
import random
from datetime import datetime

from fastapi import HTTPException

from admitplus.config import settings
from admitplus.database.redis import BaseRedisCRUD
from admitplus.api.user.user_profile_repo import UserRepo
from admitplus.api.auth.auth_schema import (
    LoginRequest,
    LoginResponse,
    SignUpResponse,
    SignUpRequest,
)
from admitplus.api.auth.token_schema import TokenResponse
from admitplus.utils.email_utils import send_verification_email
from admitplus.common.exceptions import DuplicateEmailError
from admitplus.utils.jwt_utils import create_token
from admitplus.utils.crypto_utils import (
    generate_refresh_token,
    generate_uuid,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self):
        self.user_repo = UserRepo()
        self.redis_repo = BaseRedisCRUD()
        logging.info(f"[Auth Service] Initialized with UserRepository and Redis")

    async def sign_up(self, request: SignUpRequest) -> SignUpResponse:
        try:
            logging.info(
                f"[Auth Service] [Sign Up] Starting sign up process for email: {request.email}"
            )

            now = datetime.utcnow()
            user_id = generate_uuid()

            # Validate uniqueness
            if await self.user_repo.check_email_exists(request.email):
                logging.warning(
                    f"[Auth Service] [Sign Up] Duplicate email detected: {request.email}"
                )
                raise DuplicateEmailError()

            if await self.user_repo.find_user_by_id(user_id):
                logging.error(
                    f"[Auth Service] [Sign Up] User ID collision detected: {user_id}"
                )
                raise Exception(f"User ID {user_id} already exists")

            # Verify email
            verified_key = f"email_verified:{request.email}:{settings.SIGN_UP_VERIFICATION_EMAIL.lower()}"
            if not await self.redis_repo.get(verified_key):
                logging.warning(
                    f"[Auth Service] [Sign Up] Email verification failed for: {request.email}"
                )
                raise HTTPException(
                    status_code=400,
                    detail="Email not verified. Please verify your email first.",
                )

            logging.info(
                f"[Auth Service] [Sign Up] Email verification successful for: {request.email}"
            )

            # Create users files
            user_doc = {
                "user_id": user_id,
                "email": request.email,
                "hashed_pwd": hash_password(request.password),
                "memberships": [
                    membership.dict() for membership in request.memberships
                ],
                "created_at": now,
                "updated_at": now,
                "is_verified": True,
            }

            insert_id = await self.user_repo.create_user(user_doc)

            # Validate that users creation was successful
            if not insert_id:
                logging.error(
                    f"[Auth Service] [Sign Up] Failed to create users document for users: {user_id}"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create users account. Please try again.",
                )

            logging.info(
                f"[Auth Service] [Sign Up] User document created successfully with insert id: {insert_id}"
            )

            # Clean up verification record
            try:
                await self.redis_repo.delete(verified_key)
                logging.info(
                    f"[Auth Service] [Sign Up] Email verification record cleaned up for: {request.email}"
                )
            except Exception as redis_error:
                logging.warning(
                    f"[Auth Service] [Sign Up] Failed to clean up verification record for {request.email}: {redis_error}"
                )

            # Generate authentication tokens
            role = request.memberships[0].role
            token_data = {"user_id": user_id, "email": request.email, "role": role}
            refresh_token = generate_refresh_token()

            # Store refresh token in Redis
            try:
                expire_seconds = (
                    int(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60
                )
                await self.redis_repo.hset_with_expire(
                    "refresh_tokens",
                    refresh_token,
                    json.dumps(token_data),
                    expire_seconds,
                )
                logging.info(
                    f"[Auth Service] [Sign Up] Refresh token stored in Redis for users: {user_id}"
                )
            except Exception as redis_error:
                logging.error(
                    f"[Auth Service] [Sign Up] Failed to store refresh token in Redis for users {user_id}: {redis_error}"
                )
            logging.info(
                f"[Auth Service] [Sign Up] Sign up process completed successfully for users: {user_id}"
            )
            return SignUpResponse(
                user_id=user_id,
                email=request.email,
                memberships=request.memberships,
                created_at=now,
                updated_at=now,
                token=TokenResponse(
                    access_token=create_token(token_data),
                    token_type="bearer",
                    expires_in=expire_seconds,
                    refresh_token=refresh_token,
                ),
            )
        except DuplicateEmailError:
            logging.error(
                f"[Auth Service] [Sign Up] Sign up failed - duplicate email: {request.email}"
            )
            raise
        except Exception as e:
            logging.error(
                f"[Auth Service] [Sign Up] Sign up process failed for email {request.email}: {str(e)}"
            )
            raise

    async def login(self, request: LoginRequest) -> LoginResponse:
        try:
            logging.info(
                f"[Auth Service] [Login] Processing login for email: {request.email}"
            )

            email = request.email
            password = request.password

            # Find users by email
            user_data = await self.user_repo.find_user_by_email(email)
            if not user_data:
                logging.warning(
                    f"[Auth Service] [Login] User not found for email: {email}"
                )
                raise HTTPException(status_code=401, detail="User not found")

            # Verify password
            db_password = user_data["hashed_pwd"]
            if not isinstance(db_password, str):
                logging.error(
                    f"[Auth Service] [Login] Invalid password format for agencies: {user_data['user_id']}"
                )
                raise HTTPException(
                    status_code=500, detail="Invalid stored password format"
                )

            if not verify_password(db_password, password):
                logging.warning(
                    f"[Auth Service] [Login] Incorrect password for agencies: {user_data['user_id']}"
                )
                raise HTTPException(status_code=401, detail="Incorrect password")

            # Generate tokens
            role = user_data.get("memberships", [{}])[0].get(
                "role", settings.USER_ROLE_STUDENT
            )
            token_data = {
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "role": role,
            }
            access_token = create_token(token_data)
            try:
                expire_seconds = (
                    int(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS or 1) * 24 * 60 * 60
                )
                await self.redis_repo.set(
                    f"token:{access_token}", json.dumps(token_data), expire_seconds
                )
                logging.info(
                    f"[Auth Service] [Login] Access token stored successfully for users: {user_data['user_id']}"
                )
            except Exception as redis_error:
                logging.error(
                    f"[Auth Service] [Login] Redis error storing refresh token for users {user_data['user_id']}: {redis_error}"
                )

            logging.info(
                f"[Auth Service] [Login] User {user_data['user_id']} successfully logged in"
            )
            return LoginResponse(
                user_id=user_data["user_id"],
                email=user_data["email"],
                token=TokenResponse(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=expire_seconds,
                ),
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Auth Service] [Login] Error during login: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def logout(self, user_id: str):
        try:
            logging.info(
                f"[Auth Service] [Logout] Processing logout for agencies: {user_id}"
            )

            try:
                user_tokens_key = f"user_tokens:{user_id}"
                user_tokens = await self.redis_repo.smembers(user_tokens_key)

                for token in user_tokens:
                    await self.redis_repo.delete(f"token:{token}")

                await self.redis_repo.delete(user_tokens_key)

                logging.info(
                    f"[Auth Service] [Logout] Removed {len(user_tokens)} tokens for users: {user_id}"
                )

            except Exception as redis_error:
                logging.error(
                    f"[Auth Service] [Logout] Redis error during logout for users {user_id}: {redis_error}"
                )
                # 安全策略：Redis失败时，仍然返回成功，但记录警告
                # 建议：实现token黑名单机制，或使用数据库记录登出状态
                logging.warning(
                    f"[Auth Service] [Logout] WARNING: User {user_id} logged out but tokens may still be valid due to Redis failure"
                )
        except Exception as e:
            logging.error(
                f"[Auth Service] [Logout] Error during logout for agencies {user_id}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to logout")

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            logging.info("[Auth Service] [Refresh Token] Processing token refresh")

            # Validate refresh token input
            if not refresh_token or not isinstance(refresh_token, str):
                logging.warning(
                    "[Auth Service] [Refresh Token] Invalid refresh token format"
                )
                raise HTTPException(
                    status_code=401,
                    detail="Invalid refresh token: token is empty or invalid type",
                )

            try:
                token_data = await self.redis_repo.get(f"token:{refresh_token}")

                if not token_data:
                    logging.warning(
                        "[Auth Service] [Refresh Token] Refresh token not found or expired"
                    )
                    raise HTTPException(status_code=401, detail="Invalid refresh token")

            except Exception as redis_error:
                logging.error(
                    f"[Auth Service] [Refresh Token] Redis error getting token data: {redis_error}"
                )
                raise HTTPException(
                    status_code=500, detail="Service temporarily unavailable"
                )

            # Parse token data and get agencies info
            try:
                token_info = json.loads(token_data)
                user_id = token_info.get("user_id")
                if not user_id:
                    logging.warning(
                        "[Auth Service] [Refresh Token] Invalid token data: missing user_id field"
                    )
                    raise HTTPException(status_code=401, detail="Invalid refresh token")
            except json.JSONDecodeError:
                logging.warning(
                    "[Auth Service] [Refresh Token] Invalid token data format"
                )
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            # Verify users exists in database
            user_data = await self.user_repo.find_user_by_id(user_id)
            if not user_data:
                logging.warning(
                    f"[Auth Service] [Refresh Token] User not found: {user_id}"
                )
                raise HTTPException(
                    status_code=401, detail="Invalid refresh token: agencies not found"
                )

            # Generate new tokens
            role = user_data.get("memberships", [{}])[0].get(
                "role", settings.USER_ROLE_STUDENT
            )
            new_token_data = {
                "user_id": user_data["user_id"],
                "email": user_data.get("email", ""),
                "role": role,
            }
            new_access_token = create_token(new_token_data)
            new_refresh_token = generate_refresh_token()

            try:
                user_tokens_key = f"user_tokens:{user_id}"
                user_tokens = await self.redis_repo.smembers(user_tokens_key)

                for token in user_tokens:
                    await self.redis_repo.delete(f"token:{token}")

                await self.redis_repo.delete(user_tokens_key)

                expire_seconds = (
                    int(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60
                )
                await self.redis_repo.set(
                    f"token:{new_refresh_token}",
                    json.dumps(new_token_data),
                    expire_seconds,
                )
                await self.redis_repo.sadd(user_tokens_key, new_refresh_token)

                logging.info(
                    f"[Auth Service] [Refresh Token] New refresh token stored successfully for users: {user_id}"
                )
            except Exception as redis_error:
                logging.error(
                    f"[Auth Service] [Refresh Token] Redis error managing tokens for users {user_id}: {redis_error}"
                )
                # Continue with token refresh even if Redis fails - users gets new access token
                # but refresh token functionality won't work until Redis is restored

            logging.info(
                f"[Auth Service] [Refresh Token] Successfully refreshed tokens for agencies: {user_id}"
            )
            return TokenResponse(
                access_token=new_access_token,
                token_type="bearer",
                expires_in=expire_seconds,
                refresh_token=new_refresh_token,
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Auth Service] [Refresh Token] Error during token refresh: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Internal server error during token refresh"
            )

    async def reset_password(self, email: str, password: str, code: str):
        try:
            logging.info(
                f"[Auth Service] [Reset Password] Processing password reset for email: {email}"
            )

            # Check if email has been verified (via /verify-code endpoint)
            verified_key = f"email_verified:{email}:{settings.RESET_PASSWORD_VERIFICATION_EMAIL.lower()}"
            is_verified = await self.redis_repo.get(verified_key)

            if is_verified:
                # Email already verified via /verify-code endpoint
                logging.info(
                    f"[Auth Service] [Reset Password] Using pre-verified email status for: {email}"
                )
            else:
                # Fallback: verify the code directly if not pre-verified
                redis_key = f"email_code:{email}:{settings.RESET_PASSWORD_VERIFICATION_EMAIL.lower()}"
                stored_code = await self.redis_repo.get(redis_key)

                if stored_code is None:
                    logging.warning(
                        f"[Auth Service] [Reset Password] No verification found for email: {email}"
                    )
                    raise HTTPException(
                        status_code=400, detail="Email not verified or code expired."
                    )
                if stored_code != code:
                    logging.warning(
                        f"[Auth Service] [Reset Password] Invalid code for email: {email}"
                    )
                    raise HTTPException(
                        status_code=400, detail="Invalid verification code."
                    )

                # Mark as verified and delete the code
                await self.redis_repo.set(verified_key, "true", expire=600)
                await self.redis_repo.delete(redis_key)
                logging.info(
                    f"[Auth Service] [Reset Password] Email code verified for: {email}"
                )

            # Update password in database
            modified_count = await self.user_repo.update_user_password(
                email, hash_password(password)
            )
            if modified_count < 1:
                raise HTTPException(status_code=404, detail="User not found")

            # Clean up verification status after successful password reset
            await self.redis_repo.delete(verified_key)
            logging.info(
                f"[Auth Service] [Reset Password] Password reset completed for: {email}"
            )

            return {
                "message": "Password reset successful",
                "timestamp": datetime.utcnow(),
            }
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Auth Service] [Reset Password] Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to reset password")

    async def send_verification_code(self, email: str, purpose: str):
        try:
            logging.info(
                f"[Auth Service] [Send Verification Code] Processing request for email: {email}, purpose: {purpose}"
            )

            # Validate purpose
            if purpose not in [
                settings.SIGN_UP_VERIFICATION_EMAIL,
                settings.RESET_PASSWORD_VERIFICATION_EMAIL,
            ]:
                logging.error(
                    f"[Auth Service] [Send Verification Code] Invalid email purpose: {purpose}"
                )
                raise ValueError(f"Invalid email purpose: {purpose}")

            # Generate and store verification code
            code = str(random.randint(100000, 999999))
            logging.debug(
                f"[Auth Service] [Send Verification Code] Generated code for {email}"
            )

            # Store code with purpose to avoid conflicts between different verification types
            redis_key = f"email_code:{email}:{purpose.lower()}"
            await self.redis_repo.set(redis_key, code, expire=300)  # 5 minutes
            logging.debug(
                f"[Auth Service] [Send Verification Code] Code stored in Redis for {email} with purpose {purpose}"
            )

            # Send verification email
            email_sent = send_verification_email(email, code, purpose)
            if not email_sent:
                # If email sending failed, remove the stored code to prevent inconsistency
                await self.redis_repo.delete(redis_key)
                logging.error(
                    f"[Auth Service] [Send Verification Code] Failed to send email to {email}, removed stored code"
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to send verification email. Please try again.",
                )

            logging.debug(
                f"[Auth Service] [Send Verification Code] Email sent to {email}"
            )
            logging.info(
                f"[Auth Service] [Send Verification Code] Successfully sent verification code to {email} for {purpose}"
            )
            return {
                "message": "Verification code sent.",
                "timestamp": datetime.utcnow(),
            }
        except ValueError as ve:
            logging.error(
                f"[Auth Service] [Send Verification Code] Validation error: {ve}"
            )
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logging.error(
                f"[Auth Service] [Send Verification Code] Error for {email}: {str(e)}"
            )
            raise HTTPException(
                status_code=500, detail="Failed to send verification code"
            )

    async def verify_email_code(self, email: str, purpose: str, code):
        try:
            logging.info(
                f"[Auth Service] [Verify Email Code] Processing verification for email: {email}, purpose: {purpose}"
            )

            # Validate purpose
            if purpose not in [
                settings.SIGN_UP_VERIFICATION_EMAIL,
                settings.RESET_PASSWORD_VERIFICATION_EMAIL,
            ]:
                logging.error(
                    f"[Auth Service] [Verify Email Code] Invalid email purpose: {purpose}"
                )
                raise ValueError(f"Invalid email purpose: {purpose}")

            # Get stored code from Redis
            redis_key = f"email_code:{email}:{purpose.lower()}"
            logging.debug(
                f"[Auth Service] [Verify Email Code] Looking for code in Redis key: {redis_key}"
            )
            stored_code = await self.redis_repo.get(redis_key)

            if stored_code is None:
                logging.warning(
                    f"[Auth Service] [Verify Email Code] No code found for email: {email}, purpose: {purpose}"
                )
                raise HTTPException(status_code=400, detail="Code expired or not sent.")
            if stored_code != code:
                logging.warning(
                    f"[Auth Service] [Verify Email Code] Invalid code for email: {email}"
                )
                raise HTTPException(status_code=400, detail="Invalid code.")

            verified_key = f"email_verified:{email}:{purpose.lower()}"
            await self.redis_repo.set(verified_key, "true", expire=600)
            logging.info(
                f"[Auth Service] [Verify Email Code] Set verification key: {verified_key}"
            )

            # Remove used code from Redis
            await self.redis_repo.delete(redis_key)
            logging.info(
                f"[Auth Service] [Verify Email Code] Email verification completed for: {email}"
            )

            return {
                "message": "Email verified successfully.",
                "timestamp": datetime.utcnow(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Auth Service] [Verify Email Code] Error verifying email {email}: {str(e)}"
            )
            raise HTTPException(status_code=500, detail="Failed to verify email code")

    async def set_password(self, email: str, password: str):
        try:
            logging.info(
                f"[Auth Service] [Set Password] Setting password for email: {email}"
            )

            # 直接更新密码 - 复用reset_password中已验证的update_user_password方法
            modified_count = await self.user_repo.update_user_password(
                email, hash_password(password)
            )

            if modified_count < 1:
                raise HTTPException(status_code=404, detail="User not found")

            logging.info(
                f"[Auth Service] [Set Password] Password set completed for: {email}"
            )

            return {
                "message": "Password set successfully",
                "timestamp": datetime.utcnow(),
            }
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[Auth Service] [Set Password] Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to set password")
