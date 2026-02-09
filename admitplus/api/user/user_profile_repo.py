import logging
from datetime import datetime
from typing import Optional, Dict, Any

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class UserRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.user_profiles_collection = settings.USER_PROFILES_COLLECTION

        logging.info(
            f"[User Repo] [Init] Initialized with db: {self.db_name}, collection: {self.user_profiles_collection}"
        )

        if not self.user_profiles_collection:
            logging.error(
                "[User Repo] [Init] No collection name available from environment or config!"
            )
            raise ValueError(
                "Collection name is required but not found in environment or config"
            )

        self.user_repo = BaseMongoCRUD(self.db_name)

    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new users
        """
        try:
            logging.info(
                f"[User Repo] [Create User] Creating users: {user_data.get('user_id')}"
            )

            result = await self.user_repo.insert_one(
                document=user_data, collection_name=self.user_profiles_collection
            )

            if result:
                logging.info(
                    f"[User Repo] [Create User] Successfully created users: {user_data.get('user_id')}"
                )
            else:
                logging.error(
                    f"[User Repo] [Create User] Failed to create users: {user_data.get('user_id')}"
                )
            return result
        except Exception as e:
            logging.error(f"[User Repo] [Create User] Error: {str(e)}")
            return None

    async def check_email_exists(self, email: str) -> bool:
        """
        Check if email already exists
        """
        try:
            logging.info(f"[User Repo] [Check Email Exists] Checking email: {email}")

            result = await self.user_repo.find_one(
                query={"email": email}, collection_name=self.user_profiles_collection
            )
            exists = result is not None
            logging.info(
                f"[User Repo] [Check Email Exists] Email {email} exists: {exists}"
            )
            return exists
        except Exception as e:
            logging.error(f"[User Repo] [Check Email Exists] Error: {str(e)}")
            return False

    async def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find users by email address
        """
        try:
            logging.info(
                f"[User Repo] [Find User By Email] Searching for users with email: {email}"
            )

            result = await self.user_repo.find_one(
                query={"email": email}, collection_name=self.user_profiles_collection
            )

            if result:
                logging.info(
                    f"[User Repo] [Find User By Email] Found users: {result.get('user_id')}"
                )
            else:
                logging.warning(
                    f"[User Repo] [Find User By Email] User not found with email: {email}"
                )
            return result
        except Exception as e:
            logging.error(f"[User Repo] [Find User By Email] Error: {str(e)}")
            return None

    async def find_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Find users by users ID
        """
        try:
            logging.info(
                f"[User Repo] [Find User By ID] Searching for users: {user_id}"
            )

            result = await self.user_repo.find_one(
                query={"user_id": user_id},
                collection_name=self.user_profiles_collection,
            )

            if result:
                logging.info(
                    f"[User Repo] [Find User By ID] Found users: {result.get('email')}"
                )
            else:
                logging.warning(
                    f"[User Repo] [Find User By ID] User not found: {user_id}"
                )
            return result
        except Exception as e:
            logging.error(f"[User Repo] [Find User By ID] Error: {str(e)}")
            return None

    async def update_user_password(self, email: str, hashed_password: str) -> int:
        """Update users password by email"""
        try:
            logging.info(
                f"[User Repo] [Update Password] Updating password for email: {email}"
            )

            result = await self.user_repo.update_one(
                query={"email": email},
                update={
                    "$set": {
                        "hashed_pwd": hashed_password,
                        "updated_at": datetime.utcnow(),
                    }
                },
                collection_name=self.user_profiles_collection,
            )

            if result:
                logging.info(
                    f"[User Repo] [Update Password] Successfully updated password for: {email}"
                )
            else:
                logging.warning(
                    f"[User Repo] [Update Password] No users found to update: {email}"
                )

            return result

        except Exception as e:
            logging.error(f"[User Repo] [Update Password] Error: {str(e)}")
            return 0

    async def update_user_password_by_id(
        self, user_id: str, hashed_password: str
    ) -> int:
        """
        Update users password by users ID
        """
        try:
            logging.info(
                f"[User Repo] [Update Password By ID] Updating password for users: {user_id}"
            )

            result = await self.user_repo.update_one(
                query={"user_id": user_id},
                update_data={
                    "$set": {
                        "hashed_pwd": hashed_password,
                        "updated_at": datetime.utcnow(),
                    }
                },
                collection_name=self.user_profiles_collection,
            )

            if result:
                logging.info(
                    f"[User Repo] [Update Password By ID] Successfully updated password for users: {user_id}"
                )
            else:
                logging.warning(
                    f"[User Repo] [Update Password By ID] No users found to update: {user_id}"
                )

            return result

        except Exception as e:
            logging.error(f"[User Repo] [Update Password By ID] Error: {str(e)}")
            return 0

    async def update_user_information(
        self, user_id: str, update_data: Dict[str, Any]
    ) -> int:
        """
        Update users information
        """
        try:
            logging.info(f"[User Repo] [Update User Info] Updating users: {user_id}")

            update_data["updated_at"] = datetime.utcnow()

            result = await self.user_repo.update_one(
                query={"user_id": user_id},
                update_data={"$set": update_data},
                collection_name=self.user_profiles_collection,
            )

            if result:
                logging.info(
                    f"[User Repo] [Update User Info] Successfully updated users: {user_id}"
                )
            else:
                logging.warning(
                    f"[User Repo] [Update User Info] No users found to update: {user_id}"
                )

            return result

        except Exception as e:
            logging.error(f"[User Repo] [Update User Info] Error: {str(e)}")
            return 0

    async def update_user_status(self, user_id: str, is_active: bool) -> int:
        """Update users status"""
        try:
            logging.info(
                f"[User Repo] [Update User Status] Updating users {user_id} status to {is_active}"
            )

            result = await self.user_repo.update_one(
                query={"user_id": user_id},
                update={
                    "$set": {"is_active": is_active, "updated_at": datetime.utcnow()}
                },
                collection_name=self.user_profiles_collection,
            )

            if result:
                logging.info(
                    f"[User Repo] [Update User Status] Successfully updated users {user_id} status"
                )
            else:
                logging.warning(
                    f"[User Repo] [Update User Status] No users found with user_id: {user_id}"
                )
            return result

        except Exception as e:
            logging.error(
                f"[User Repo] [Update User Status] Error updating users status: {str(e)}"
            )
            return 0

    async def find_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Find user_id by email address
        """
        try:
            logging.info(
                f"[User Repo] [Find User ID By Email] Searching for user_id with email: {email}"
            )

            result = await self.user_repo.find_one(
                query={"email": email}, collection_name=self.user_profiles_collection
            )

            if result:
                user_id = result.get("user_id")
                logging.info(
                    f"[User Repo] [Find User ID By Email] Found user_id: {user_id} for email: {email}"
                )
                return user_id
            else:
                logging.warning(
                    f"[User Repo] [Find User ID By Email] User not found with email: {email}"
                )
                return None
        except Exception as e:
            logging.error(f"[User Repo] [Find User ID By Email] Error: {str(e)}")
            return None
