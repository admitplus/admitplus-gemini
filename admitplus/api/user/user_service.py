import logging
from datetime import datetime

from fastapi import HTTPException
from typing import Dict, Any, Optional

from .user_profile_repo import UserRepo
from .user_schema import (
    UserProfile,
    Membership,
    UserUpdateRequest,
    PasswordUpdateRequest,
    PasswordUpdateResponse,
    UserSettings,
    UserSettingsUpdateRequest,
    SecurityInfo,
)
from admitplus.utils.validation_utils import ValidationUtils
from admitplus.utils.crypto_utils import generate_uuid, hash_password, verify_password


class UserService:
    def __init__(self):
        self.user_repo = UserRepo()
        logging.info(f"[User Service] Initialized with repositories")

    async def _validate_user_exists(self, user_id: str) -> dict:
        """Validate users exists and return users data"""
        user = await self.user_repo.find_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """
        Get users's profile information
        """
        try:
            logging.info(
                f"[User Service] [Get User Profile] Getting profile for users {user_id}"
            )

            # Validate users exists
            user = await self._validate_user_exists(user_id)

            # Convert memberships from database format to Membership objects
            memberships = []
            if user.get("memberships"):
                for membership_data in user["memberships"]:
                    memberships.append(
                        Membership(
                            role=membership_data.get("role", ""),
                            status=membership_data.get("status", "active"),
                            agency_id=membership_data.get("agency_id", ""),
                        )
                    )

            return UserProfile(
                user_id=user["user_id"],
                email=user.get("email"),
                hashed_pwd=None,  # Never return password hash in profile responses
                memberships=memberships,
                created_at=user.get("created_at"),
                updated_at=user.get("updated_at"),
                is_verified=user.get("is_verified", False),
                status=user.get("status", "active"),
                phone_number=user.get("phone_number"),
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
            )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Get User Profile] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve users profile"
            )

    async def update_user_profile(
        self, user_id: str, request: UserUpdateRequest
    ) -> UserProfile:
        """
        Update users's profile information
        """
        try:
            logging.info(
                f"[User Service] [Update User Profile] Updating profile for users {user_id}"
            )

            # Validate users exists
            await self._validate_user_exists(user_id)

            # Validate input data
            if request.email is not None and not ValidationUtils.validate_email_format(
                request.email
            ):
                raise HTTPException(status_code=400, detail="Invalid email format")

            if (
                request.phone_number is not None
                and not ValidationUtils.validate_phone_number(request.phone_number)
            ):
                raise HTTPException(
                    status_code=400, detail="Invalid phone number format"
                )

            if request.first_name is not None:
                ValidationUtils.validate_name(request.first_name, "First name")

            if request.last_name is not None:
                ValidationUtils.validate_name(request.last_name, "Last name")

            # Prepare update data
            update_data = {}
            if request.email is not None:
                update_data["email"] = request.email
            if request.phone_number is not None:
                update_data["phone_number"] = request.phone_number
            if request.first_name is not None:
                update_data["first_name"] = request.first_name.strip()
            if request.last_name is not None:
                update_data["last_name"] = request.last_name.strip()

            if not update_data:
                raise HTTPException(status_code=400, detail="No fields to update")

            update_data["updated_at"] = datetime.utcnow()

            # Update users
            result = await self.user_repo.update_user_information(user_id, update_data)
            if result == 0:
                raise HTTPException(
                    status_code=500, detail="Failed to update users profile"
                )

            # Get updated users profile
            updated_user = await self.get_user_profile(user_id)
            return updated_user

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Update User Profile] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to update users profile"
            )

    async def update_user_password(
        self, user_id: str, request: PasswordUpdateRequest
    ) -> PasswordUpdateResponse:
        """Update users's password"""
        try:
            logging.info(
                f"[User Service] [Update Password] Updating password for users {user_id}"
            )

            # 1. Validate users exists
            user = await self._validate_user_exists(user_id)

            # 2. Verify current password (security check)
            stored_password_hash = user.get("hashed_pwd")
            if not stored_password_hash:
                raise HTTPException(
                    status_code=400, detail="No password set for this users"
                )

            if not verify_password(stored_password_hash, request.current_password):
                raise HTTPException(
                    status_code=400, detail="Current password is incorrect"
                )

            # 3. Validate password confirmation
            if request.new_password != request.confirm_password:
                raise HTTPException(
                    status_code=400, detail="New password and confirmation do not match"
                )

            # 4. Validate new password strength
            if len(request.new_password) < 8:
                raise HTTPException(
                    status_code=400,
                    detail="New password must be at least 8 characters long",
                )

            if len(request.new_password) > 128:
                raise HTTPException(
                    status_code=400,
                    detail="New password is too long (max 128 characters)",
                )

            # 5. Check if new password is different from current password
            if verify_password(stored_password_hash, request.new_password):
                raise HTTPException(
                    status_code=400,
                    detail="New password must be different from current password",
                )

            # 6. Hash the new password
            hashed_password = hash_password(request.new_password)

            # 7. Update password in database
            result = await self.user_repo.update_user_password_by_id(
                user_id, hashed_password
            )
            if result == 0:
                raise HTTPException(status_code=500, detail="Failed to update password")

            return PasswordUpdateResponse(
                success=True,
                message="Password updated successfully",
                updated_at=datetime.utcnow(),
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Update Password] Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update password")

    async def get_user_settings(self, user_id: str) -> UserSettings:
        """Get users's account settings"""
        try:
            logging.info(
                f"[User Service] [Get User Settings] Getting settings for users {user_id}"
            )

            # Validate users exists
            user = await self._validate_user_exists(user_id)

            # Get users settings from database (with defaults if not set)
            settings_data = user.get("settings", {})

            return UserSettings(
                language=settings_data.get("language", "en"),
                timezone=settings_data.get("timezone", "UTC"),
                date_format=settings_data.get("date_format", "YYYY-MM-DD"),
                theme=settings_data.get("theme", "light"),
                notifications=settings_data.get("notifications", {}),
                privacy=settings_data.get("privacy", {}),
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Get User Settings] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve users settings"
            )

    async def update_user_settings(
        self, user_id: str, request: UserSettingsUpdateRequest
    ) -> UserSettings:
        """Update users's account settings"""
        try:
            logging.info(
                f"[User Service] [Update User Settings] Updating settings for users {user_id}"
            )

            # Validate users exists
            user = await self._validate_user_exists(user_id)

            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}
            settings_data = user.get("settings", {})

            # Update settings fields
            if request.language is not None:
                settings_data["language"] = request.language
            if request.timezone is not None:
                settings_data["timezone"] = request.timezone
            if request.date_format is not None:
                settings_data["date_format"] = request.date_format
            if request.theme is not None:
                settings_data["theme"] = request.theme
            if request.notifications is not None:
                settings_data["notifications"] = request.notifications.dict()
            if request.privacy is not None:
                settings_data["privacy"] = request.privacy.dict()

            update_data["settings"] = settings_data

            # Update users settings in database
            result = await self.user_repo.update_user_information(user_id, update_data)
            if result == 0:
                raise HTTPException(
                    status_code=500, detail="Failed to update users settings"
                )

            # Get updated settings
            updated_settings = await self.get_user_settings(user_id)
            return updated_settings

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Update User Settings] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to update users settings"
            )

    async def get_user_security_info(self, user_id: str) -> SecurityInfo:
        """Get users's security information"""
        try:
            logging.info(
                f"[User Service] [Get Security Info] Getting security info for users {user_id}"
            )

            # Validate users exists
            user = await self._validate_user_exists(user_id)

            # Get security information
            security_data = user.get("security", {})

            return SecurityInfo(
                two_factor_enabled=security_data.get("two_factor_enabled", False),
                last_password_change=security_data.get("last_password_change"),
                last_login=user.get("last_login_at"),
                login_attempts=security_data.get("login_attempts", 0),
                account_locked=security_data.get("account_locked", False),
                email_verified=user.get("email_verified", False),
                phone_verified=user.get("phone_verified", False),
                trusted_devices=security_data.get("trusted_devices", 0),
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Get Security Info] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve security information"
            )

    # ========== 创建新user ==========

    async def create_user(self, user_data: Dict[str, Any]) -> UserProfile:
        """
        Create a new user - 根据您实际的数据库结构调整
        """
        try:
            logging.info(
                f"[User Service] [Create User] Creating new user with email: {user_data.get('email')}"
            )

            # 验证必需字段
            if not user_data.get("email"):
                raise HTTPException(status_code=400, detail="Email is required")

            # 验证邮箱格式
            if not ValidationUtils.validate_email_format(user_data["email"]):
                raise HTTPException(status_code=400, detail="Invalid email format")

            # 检查邮箱是否已存在
            existing_user = await self.user_repo.find_user_by_email(user_data["email"])
            if existing_user:
                raise HTTPException(
                    status_code=400, detail="User with this email already exists"
                )

            # 生成用户 ID
            user_id = generate_uuid()

            # 根据您实际的数据库结构准备数据
            create_data = {
                "user_id": user_id,
                "email": user_data["email"].lower().strip(),
                "is_verified": user_data.get("is_verified", False),
                "status": user_data.get("status", "active"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # 处理密码（如果提供）
            if user_data.get("password"):
                ValidationUtils.validate_string_length(
                    user_data["password"], "Password", max_length=128, min_length=8
                )
                create_data["hashed_pwd"] = hash_password(user_data["password"])

            # 设置默认的 memberships（根据您的数据结构）
            create_data["memberships"] = user_data.get("memberships", [])

            # 创建用户
            created_user = await self.user_repo.create_user(create_data)
            if not created_user:
                raise HTTPException(status_code=500, detail="Failed to create user")

            logging.info(
                f"[User Service] [Create User] Successfully created user: {user_id}"
            )

            # Return user profile
            return UserProfile(
                user_id=user_id,
                email=create_data.get("email"),
                hashed_pwd=None,  # Never return password hash
                memberships=[
                    Membership(**m) for m in create_data.get("memberships", [])
                ],
                created_at=create_data.get("created_at"),
                updated_at=create_data.get("updated_at"),
                is_verified=create_data.get("is_verified", False),
                status=create_data.get("status", "active"),
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Create User] Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create user")

    async def create_user_with_password(
        self, email: str, password: str, status: str = "active"
    ) -> UserProfile:
        """
        Create a new user with email and password
        """
        user_data = {"email": email, "password": password, "status": status}
        return await self.create_user(user_data)

    async def create_user_without_password(
        self, email: str, status: str = "active"
    ) -> UserProfile:
        """
        Create a new user without setting a password (for SSO or external auth)
        """
        user_data = {"email": email, "status": status}
        return await self.create_user(user_data)

    async def get_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Get user_id by email address
        """
        try:
            logging.info(
                f"[User Service] [Get User ID By Email] Getting user_id for email: {email}"
            )

            # Validate email format
            if not ValidationUtils.validate_email_format(email):
                raise HTTPException(status_code=400, detail="Invalid email format")

            # Find user_id by email
            user_id = await self.user_repo.find_user_id_by_email(email)
            return user_id

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"[User Service] [Get User ID By Email] Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve user_id by email"
            )
