import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class ApplicationRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        self.student_application_collection = settings.STUDENT_APPLICATIONS_COLLECTION
        logging.info(
            f"[Application Repo] Initialized with db: {self.db_name}, collection: {self.student_application_collection}"
        )

    async def create_application(
        self, application_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create new application
        """
        try:
            logging.info(
                f"[Application Repo] [Create Application] Creating application"
            )

            # Add application-specific fields
            # Note: status is already set by service, but ensure it's set if missing
            if "status" not in application_data:
                application_data["status"] = "planning"
            application_data["created_at"] = datetime.utcnow()
            application_data["updated_at"] = datetime.utcnow()

            insert_id = await self.mongo_repo.insert_one(
                application_data, collection_name=self.student_application_collection
            )

            if insert_id:
                logging.info(
                    f"[Application Repo] [Create Application] Successfully created application: {insert_id}"
                )
            return insert_id

        except Exception as e:
            logging.error(f"[Application Repo] [Create Application] Error: {str(e)}")
            return None

    async def find_applications_by_student(
        self, student_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find all applications for a students
        """
        try:
            logging.info(
                f"[Application Repo] [Find By Student] Finding applications for students: {student_id}"
            )

            result = await self.mongo_repo.find_many(
                query={"student_id": student_id, "status": {"$ne": "deleted"}},
                collection_name=self.student_application_collection,
            )
            logging.info(
                f"[Application Repo] [Find By Student] Found {len(result)} applications for students: {student_id}"
            )
            return result

        except Exception as e:
            logging.error(f"[Application Repo] [Find By Student] Error: {str(e)}")
            return []

    async def find_application_by_id(
        self, application_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find application by application id
        """
        try:
            logging.info(
                f"[Application Repo] [Find By ID] Finding application: {application_id}"
            )

            result = await self.mongo_repo.find_one(
                query={"application_id": application_id},
                collection_name=self.student_application_collection,
            )

            if result:
                logging.info(
                    f"[Application Repo] [Find By ID] Found application: {application_id}"
                )
            else:
                logging.warning(
                    f"[Application Repo] [Find By ID] Application not found: {application_id}"
                )

            return result

        except Exception as e:
            logging.error(f"[Application Repo] [Find By ID] Error: {str(e)}")
            return None

    async def update_application(
        self, application_id: str, update_data: Dict[str, Any]
    ) -> int:
        """
        Update application with provided data
        """
        try:
            logging.info(
                f"[Application Repo] [Update Application] Updating application {application_id}"
            )

            update_data["updated_at"] = datetime.utcnow()
            result = await self.mongo_repo.update_one(
                query={"application_id": application_id},
                update={"$set": update_data},
                collection_name=self.student_application_collection,
            )

            if result:
                logging.info(
                    f"[Application Repo] [Update Application] Successfully updated application {application_id}"
                )
            return result

        except Exception as e:
            logging.error(f"[Application Repo] [Update Application] Error: {str(e)}")
            return 0

    async def delete_application(
        self, application_id: str, update_data: Dict[str, Any]
    ) -> int:
        """
        Soft delete application by updating its status and other fields
        This performs an update operation, not a hard delete
        """
        try:
            logging.info(
                f"[Application Repo] [Delete Application] Soft deleting application {application_id}"
            )

            update_data["updated_at"] = datetime.utcnow()
            result = await self.mongo_repo.update_one(
                query={"application_id": application_id},
                update={"$set": update_data},
                collection_name=self.student_application_collection,
            )

            if result:
                logging.info(
                    f"[Application Repo] [Delete Application] Successfully soft deleted application {application_id}"
                )
            return result

        except Exception as e:
            logging.error(f"[Application Repo] [Delete Application] Error: {str(e)}")
            return 0
