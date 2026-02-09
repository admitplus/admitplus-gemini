import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD
from admitplus.database.redis import BaseRedisCRUD
from .invite_schema import InviteType


class InviteRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.redis_repo = BaseRedisCRUD()

        # Collection name for invites
        self.invites_collection = settings.INVITATIONS_COLLECTION

        logging.info(
            f"[Invite Repo] Initialized with db: {self.db_name}, collection: {self.invites_collection}"
        )

    async def find_emails_by_contract_status(
        self, teacher_id: str
    ) -> Dict[str, List[str]]:
        """
        根据 teacher_id 查找邮箱，按 contract_status 分组返回
        对 contracted 状态进行二次分类，基于 status 字段分组

        Args:
            teacher_id: 教师ID

        Returns:
            {
                "contracted": {
                    "accepted": ["email1@example.com", "email2@example.com"],
                    "pending": ["email3@example.com", "email4@example.com"]
                },
                "trial": ["email5@example.com", "email6@example.com"]
            }
        """
        try:
            logging.info(
                f"[Invite Repo] [Find Emails By Contract Status] Finding emails for teacher {teacher_id}"
            )

            # 查询所有匹配的邀请记录
            invites = await self.mongo_repo.find_many(
                query={"teacher_id": teacher_id},
                collection_name=self.invites_collection,
            )

            # 按 contract_status 和 status 分组邮箱
            contracted_accepted_emails = []
            contracted_pending_emails = []
            trial_emails = []

            for invite in invites:
                email = invite.get("email")
                contract_status = invite.get("contract_status")
                status = invite.get("status")

                if not email:
                    continue

                if contract_status == "contracted":
                    if status == "accepted":
                        contracted_accepted_emails.append(email)
                    else:
                        # 包括 pending, expired, revoked 等未接受状态
                        contracted_pending_emails.append(email)
                elif contract_status == "trial":
                    trial_emails.append(email)

            result = {
                "contracted": {
                    "accepted": contracted_accepted_emails,
                    "pending": contracted_pending_emails,
                },
                "trial": trial_emails,
            }

            logging.info(
                f"[Invite Repo] [Find Emails By Contract Status] "
                f"Found {len(contracted_accepted_emails)} accepted contracted, "
                f"{len(contracted_pending_emails)} pending contracted, and "
                f"{len(trial_emails)} trial emails for teacher {teacher_id}"
            )
            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Find Emails By Contract Status] Error finding emails for teacher {teacher_id}: {str(e)}"
            )
            return {"contracted": {"accepted": [], "pending": []}, "trial": []}

    async def find_pending_invite(
        self, email: str, agency_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find pending invite for email and agencies
        """
        try:
            logging.info(
                f"[Invite Repo] [Find Pending Invite] Finding pending invite for {email} and agencies {agency_id}"
            )

            result = await self.mongo_repo.find_one(
                query={"email": email, "agency_id": agency_id, "status": "pending"},
                collection_name=self.invites_collection,
            )

            if result:
                logging.info(
                    f"[Invite Repo] [Find Pending Invite] Found pending invite for {email} (invite_id: {result.get('invite_id', 'unknown')})"
                )
            else:
                logging.info(
                    f"[Invite Repo] [Find Pending Invite] No pending invite found for {email}"
                )

            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Find Pending Invite] Error finding pending invite for {email}: {str(e)}"
            )
            return None

    async def create_invite(self, invite_data: Dict[str, Any]) -> Optional[str]:
        """
        Create invite (agencies or students)
        """
        try:
            invite_type = invite_data.get("invite_type", "unknown")
            email = invite_data.get("email", "unknown")
            logging.info(
                f"[Invite Repo] [Create Invite] Creating {invite_type} invite for {email}"
            )

            result = await self.mongo_repo.insert_one(
                document=invite_data, collection_name=self.invites_collection
            )

            if result:
                logging.info(
                    f"[Invite Repo] [Create Invite] Successfully created {invite_type} invite for {email}: {result}"
                )
            else:
                logging.warning(
                    f"[Invite Repo] [Create Invite] Failed to create {invite_type} invite for {email}"
                )
            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Create Invite] Error creating {invite_type} invite for {email}: {str(e)}"
            )
            return None

    async def find_invite_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Find invite by token
        """
        try:
            logging.info(f"[Invite Repo] [Find By Token] Finding invite with token")

            # Find invite in unified collection
            invite = await self.mongo_repo.find_one(
                query={"token": token}, collection_name=self.invites_collection
            )

            if invite:
                # Set collection type based on invite_type field
                invite_type = invite.get("invite_type", "agencies")
                invite["_collection"] = invite_type
                email = invite.get("email", "unknown")
                logging.info(
                    f"[Invite Repo] [Find By Token] Found {invite_type} invite for {email}"
                )
                return invite

            logging.warning(f"[Invite Repo] [Find By Token] No invite found with token")
            return None

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Find By Token] Error finding invite by token: {str(e)}"
            )
            return None

    async def update_invite_status(self, invite_id: str, status: str) -> int:
        """
        Update invite status
        """
        try:
            logging.info(
                f"[Invite Repo] [Update Status] Updating invite {invite_id} to status {status}"
            )

            # Prepare update data
            update_data = {"$set": {"status": status, "updated_at": datetime.utcnow()}}

            # Only set accepted_at when status is "accepted"
            if status == "accepted":
                update_data["$set"]["accepted_at"] = datetime.utcnow()

            result = await self.mongo_repo.update_one(
                query={"invite_id": invite_id},
                update=update_data,
                collection_name=self.invites_collection,
            )

            if result:
                logging.info(
                    f"[Invite Repo] [Update Status] Successfully updated invite {invite_id} to {status}"
                )
            else:
                logging.warning(
                    f"[Invite Repo] [Update Status] No invite found with invite_id: {invite_id}"
                )
            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Update Status] Error updating invite {invite_id}: {str(e)}"
            )
            return 0

    async def set_invite_token(
        self,
        token: str,
        invite_id: str,
        expire_seconds: int,
        invite_type: str = "agencies",
    ) -> bool:
        """
        Set invite token in Redis
        """
        try:
            logging.info(
                f"[Invite Repo] [Set Token] Setting {invite_type} token for invite {invite_id}"
            )

            # Use different Redis keys for different invite types
            redis_key = f"{invite_type}_invite_token:{token}"

            await self.redis_repo.set(redis_key, invite_id, expire=expire_seconds)

            logging.info(
                f"[Invite Repo] [Set Token] Successfully set {invite_type} token"
            )
            return True

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Set Token] Error setting {invite_type} token: {str(e)}"
            )
            return False

    async def get_invite_token(self, token: str) -> Optional[str]:
        """
        Get invite ID from token
        """
        try:
            logging.info(f"[Invite Repo] [Get Token] Getting invite ID for token")

            # Try agencies invite token first
            invite_id = await self.redis_repo.get(f"agency_invite_token:{token}")
            if not invite_id:
                # Try students invite token
                invite_id = await self.redis_repo.get(f"student_invite_token:{token}")

            if invite_id:
                logging.info(f"[Invite Repo] [Get Token] Found invite ID: {invite_id}")
            else:
                logging.warning(
                    f"[Invite Repo] [Get Token] No invite ID found for token"
                )

            return invite_id

        except Exception as e:
            logging.error(f"[Invite Repo] [Get Token] Error: {str(e)}")
            return None

    async def delete_invite_token(self, token: str) -> bool:
        """
        Delete invite token from Redis
        """
        try:
            logging.info(f"[Invite Repo] [Delete Token] Deleting token")

            # Delete both agencies and students invite tokens
            await self.redis_repo.delete(f"agency_invite_token:{token}")
            await self.redis_repo.delete(f"student_invite_token:{token}")

            logging.info(f"[Invite Repo] [Delete Token] Successfully deleted token")
            return True

        except Exception as e:
            logging.error(f"[Invite Repo] [Delete Token] Error: {str(e)}")
            return False

    async def find_pending_invites_by_teacher_id(
        self, teacher_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find all pending student invites for a teacher
        """
        try:
            logging.info(
                f"[Invite Repo] [Find Pending Invites By Teacher] Finding pending invites for teacher {teacher_id}"
            )

            result = await self.mongo_repo.find_many(
                query={
                    "teacher_id": teacher_id.strip(),
                    "status": "pending",
                    "invite_type": InviteType.STUDENT,
                },
                sort={"created_at": -1},  # Sort by created_at descending (newest first)
                collection_name=self.invites_collection,
            )

            if result:
                logging.info(
                    f"[Invite Repo] [Find Pending Invites By Teacher] Found {len(result)} pending invites for teacher {teacher_id}"
                )
            else:
                logging.info(
                    f"[Invite Repo] [Find Pending Invites By Teacher] No pending invites found for teacher {teacher_id}"
                )

            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Find Pending Invites By Teacher] Error finding pending invites for teacher {teacher_id}: {str(e)}"
            )
            return []

    async def find_invite_by_id(self, invite_id: str) -> Optional[Dict[str, Any]]:
        """
        Find invite by invite_id
        """
        try:
            logging.info(
                f"[Invite Repo] [Find By ID] Finding invite with invite_id: {invite_id}"
            )

            result = await self.mongo_repo.find_one(
                query={"invite_id": invite_id}, collection_name=self.invites_collection
            )

            if result:
                logging.info(
                    f"[Invite Repo] [Find By ID] Found invite {invite_id} for {result.get('email', 'unknown')}"
                )
            else:
                logging.info(
                    f"[Invite Repo] [Find By ID] No invite found with invite_id: {invite_id}"
                )

            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Find By ID] Error finding invite by invite_id {invite_id}: {str(e)}"
            )
            return None

    async def revoke_invite(self, invite_id: str) -> int:
        """
        Revoke an invite by updating its status to revoked and deleting the token from Redis
        """
        try:
            logging.info(f"[Invite Repo] [Revoke Invite] Revoking invite {invite_id}")

            # First, get the invite to get the token
            invite = await self.find_invite_by_id(invite_id)
            if not invite:
                logging.warning(
                    f"[Invite Repo] [Revoke Invite] Invite {invite_id} not found"
                )
                return 0

            # Update status to revoked
            result = await self.update_invite_status(invite_id, "revoked")

            if result > 0:
                # Delete token from Redis if it exists
                token = invite.get("token")
                if token:
                    await self.delete_invite_token(token)
                    logging.info(
                        f"[Invite Repo] [Revoke Invite] Deleted token from Redis for invite {invite_id}"
                    )

                logging.info(
                    f"[Invite Repo] [Revoke Invite] Successfully revoked invite {invite_id}"
                )
            else:
                logging.warning(
                    f"[Invite Repo] [Revoke Invite] Failed to revoke invite {invite_id}"
                )

            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Revoke Invite] Error revoking invite {invite_id}: {str(e)}"
            )
            return 0

    async def delete_invite(self, invite_id: str) -> int:
        """
        Delete an invite from MongoDB and Redis
        """
        try:
            logging.info(f"[Invite Repo] [Delete Invite] Deleting invite {invite_id}")

            # First, get the invite to get the token
            invite = await self.find_invite_by_id(invite_id)
            if not invite:
                logging.warning(
                    f"[Invite Repo] [Delete Invite] Invite {invite_id} not found"
                )
                return 0

            # Delete token from Redis if it exists
            token = invite.get("token")
            if token:
                await self.delete_invite_token(token)
                logging.info(
                    f"[Invite Repo] [Delete Invite] Deleted token from Redis for invite {invite_id}"
                )

            # Delete invite from MongoDB
            result = await self.mongo_repo.delete_one(
                query={"invite_id": invite_id}, collection_name=self.invites_collection
            )

            if result > 0:
                logging.info(
                    f"[Invite Repo] [Delete Invite] Successfully deleted invite {invite_id}"
                )
            else:
                logging.warning(
                    f"[Invite Repo] [Delete Invite] Failed to delete invite {invite_id}"
                )

            return result

        except Exception as e:
            logging.error(
                f"[Invite Repo] [Delete Invite] Error deleting invite {invite_id}: {str(e)}"
            )
            return 0
