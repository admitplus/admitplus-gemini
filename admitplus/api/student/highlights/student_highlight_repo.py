import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD


class StudentHighlightRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)
        self.student_highlights_collection = settings.STUDENT_HIGHLIGHTS_COLLECTION
        logging.info(
            f"[Student Highlight Repo] Initialized with db: {self.db_name}, collection: {self.student_highlights_collection}"
        )

    async def create_student_highlight(
        self,
        student_id: str,
        created_by_member_id: str,
        highlight_id: str,
        highlight_data: Dict[str, Any],
    ) -> Optional[str]:
        """
        Create a new student highlight
        """
        try:
            logging.info(
                f"[Student Highlight Repo] [Create Student Highlight] Creating highlight: {highlight_id} for student: {student_id}"
            )

            now = datetime.utcnow()
            data = {
                "highlight_id": highlight_id,
                "student_id": student_id,
                "created_by_member_id": created_by_member_id,
                **highlight_data,
                "created_at": now,
                "updated_at": now,
            }

            insert_id = await self.mongo_repo.insert_one(
                document=data, collection_name=self.student_highlights_collection
            )

            if insert_id:
                logging.info(
                    f"[Student Highlight Repo] [Create Student Highlight] Successfully created highlight: {highlight_id}"
                )
            else:
                logging.error(
                    f"[Student Highlight Repo] [Create Student Highlight] Failed to create highlight: {highlight_id}"
                )

            return insert_id

        except Exception as e:
            logging.error(
                f"[Student Highlight Repo] [Create Student Highlight] Error: {str(e)}"
            )
            return None

    async def find_student_highlights(
        self,
        student_id: str,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        q: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Find student highlights with pagination, category filter, and text search
        """
        try:
            logging.info(
                f"[Student Highlight Repo] [Find Student Highlights] Finding highlights for student_id: {student_id}, page: {page}, page_size: {page_size}, category: {category}, q: {q}"
            )

            # Build query
            query = {"student_id": student_id}

            # Add category filter if provided
            if category:
                query["category"] = category
                logging.info(
                    f"[Student Highlight Repo] [Find Student Highlights] Filtering by category: {category}"
                )

            # Add text search filter if provided
            if q:
                search_pattern = {"$regex": q, "$options": "i"}
                query["text"] = search_pattern
                logging.info(
                    f"[Student Highlight Repo] [Find Student Highlights] Filtering by search query: {q}"
                )

            highlights, total_count = await self.mongo_repo.find_many_paginated(
                query=query,
                page=page,
                page_size=page_size,
                sort=[("created_at", -1)],
                projection={"_id": 0},
                collection_name=self.student_highlights_collection,
            )

            logging.info(
                f"[Student Highlight Repo] [Find Student Highlights] Found {len(highlights)}/{total_count} highlights for student_id: {student_id}"
            )
            return highlights, total_count
        except Exception as e:
            logging.error(
                f"[Student Highlight Repo] [Find Student Highlights] Error: {str(e)}"
            )
            return [], 0

    async def update_student_highlight(
        self, highlight_id: str, highlight_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a student highlight and return the updated document
        """
        try:
            logging.info(
                f"[Student Highlight Repo] [Update Student Highlight] Updating highlight: {highlight_id}"
            )

            # Filter out None values
            update_data = {k: v for k, v in highlight_data.items() if v is not None}
            if not update_data:
                logging.warning(
                    f"[Student Highlight Repo] [Update Student Highlight] No data to update for highlight: {highlight_id}"
                )
                return None

            update_data["updated_at"] = datetime.utcnow()

            modified_count = await self.mongo_repo.update_one(
                query={"highlight_id": highlight_id},
                update={"$set": update_data},
                collection_name=self.student_highlights_collection,
            )

            if modified_count == 0:
                logging.warning(
                    f"[Student Highlight Repo] [Update Student Highlight] No highlight found with ID: {highlight_id}"
                )
                return None

            # Fetch and return the updated document
            updated_highlight = await self.mongo_repo.find_one(
                query={"highlight_id": highlight_id},
                projection={"_id": 0},
                collection_name=self.student_highlights_collection,
            )

            if updated_highlight:
                logging.info(
                    f"[Student Highlight Repo] [Update Student Highlight] Successfully updated highlight: {highlight_id}"
                )
            else:
                logging.warning(
                    f"[Student Highlight Repo] [Update Student Highlight] Updated but could not fetch highlight: {highlight_id}"
                )

            return updated_highlight

        except Exception as e:
            logging.error(
                f"[Student Highlight Repo] [Update Student Highlight] Error: {str(e)}"
            )
            return None
