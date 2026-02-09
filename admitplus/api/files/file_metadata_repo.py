import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from admitplus.config import settings
from admitplus.database.mongo import BaseMongoCRUD
from .file_schema import FileListResponse, FileMetadataResponse


class FileRepo:
    def __init__(self):
        self.db_name = settings.MONGO_APPLICATION_WAREHOUSE_DB_NAME
        self.mongo_repo = BaseMongoCRUD(self.db_name)

        # File collections
        self.application_documents_collection = (
            settings.APPLICATION_DOCUMENTS_COLLECTION
        )
        self.user_avatars_collection = settings.USER_AVATARS_COLLECTION
        self.file_metadata_collection = settings.FILE_METADATA_COLLECTION
        self.files_storage_collection = settings.FILES_STORAGE_COLLECTION

        logging.info(f"[File Repo] Initialized with db: {self.db_name}")
        logging.info(
            f"[File Repo] Collections - Application Documents: {self.application_documents_collection}"
        )
        logging.info(
            f"[File Repo] Collections - User Avatars: {self.user_avatars_collection}"
        )
        logging.info(
            f"[File Repo] Collections - File Metadata: {self.file_metadata_collection}"
        )
        logging.info(
            f"[File Repo] Collections - Files Storage: {self.files_storage_collection}"
        )

    async def insert_file(
        self, file_data: Dict[str, Any], collection_name: str = None
    ) -> Optional[str]:
        """
        Insert a new files record
        """
        try:
            file_id = file_data.get("file_id")
            file_name = file_data.get("file_name")
            file_size = file_data.get("size")
            file_type = file_data.get("file_type")

            logging.info(f"[File Repo] [Insert File] Starting files insertion")
            logging.info(
                f"[File Repo] [Insert File] File details - ID: {file_id}, Name: {file_name}, Size: {file_size} bytes, Type: {file_type}"
            )

            # Use provided collection or default to file_metadata
            collection = collection_name or self.file_metadata_collection
            logging.info(f"[File Repo] [Insert File] Using collection: {collection}")

            result = await self.mongo_repo.insert_one(
                document=file_data, collection_name=collection
            )

            if result:
                logging.info(
                    f"[File Repo] [Insert File] Successfully inserted files: {file_id} in collection: {collection}"
                )
                logging.info(f"[File Repo] [Insert File] Insert result: {result}")
            else:
                logging.error(
                    f"[File Repo] [Insert File] Failed to insert files: {file_id} in collection: {collection}"
                )
                logging.error(f"[File Repo] [Insert File] Insert result was None")

            return result

        except Exception as e:
            logging.error(f"[File Repo] [Insert File] Error inserting files: {str(e)}")
            logging.error(f"[File Repo] [Insert File] File data: {file_data}")
            raise

    async def find_file_by_id(
        self, file_id: str, collection_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find files by ID (excluding soft-deleted ones)
        """
        try:
            logging.info(f"[File Repo] [Find By ID] Starting files lookup")
            logging.info(f"[File Repo] [Find By ID] Looking for files ID: {file_id}")

            # Use provided collection or default to file_metadata
            collection = collection_name or self.file_metadata_collection
            logging.info(
                f"[File Repo] [Find By ID] Searching in collection: {collection}"
            )

            result = await self.mongo_repo.find_one(
                query={"file_id": file_id, "deleted": {"$ne": True}},
                collection_name=collection,
            )

            if result:
                file_name = result.get("file_name")
                file_size = result.get("size")
                file_type = result.get("file_type")
                status = result.get("status")
                logging.info(
                    f"[File Repo] [Find By ID] Found files: {file_id} in collection: {collection}"
                )
                logging.info(
                    f"[File Repo] [Find By ID] File details - Name: {file_name}, Size: {file_size} bytes, Type: {file_type}, Status: {status}"
                )
            else:
                logging.warning(
                    f"[File Repo] [Find By ID] File not found: {file_id} in collection: {collection}"
                )
                logging.warning(
                    f"[File Repo] [Find By ID] File may be deleted or does not exist"
                )

            return result

        except Exception as e:
            logging.error(f"[File Repo] [Find By ID] Error finding files: {str(e)}")
            logging.error(
                f"[File Repo] [Find By ID] File ID: {file_id}, Collection: {collection_name}"
            )
            raise

    async def soft_delete_file(
        self, file_id: str, deleted_by: str, collection_name: str = None
    ) -> int:
        """
        Soft delete a files by marking it as deleted
        """
        try:
            logging.info(f"[File Repo] [Soft Delete] Starting soft delete operation")
            logging.info(
                f"[File Repo] [Soft Delete] File ID: {file_id}, Deleted by: {deleted_by}"
            )

            # Use provided collection or default to file_metadata
            collection = collection_name or self.file_metadata_collection
            logging.info(f"[File Repo] [Soft Delete] Using collection: {collection}")

            update_data = {
                "$set": {
                    "deleted": True,
                    "deleted_at": datetime.utcnow(),
                    "deleted_by": deleted_by,
                    "status": "deleted",
                }
            }
            logging.info(f"[File Repo] [Soft Delete] Update data: {update_data}")

            result = await self.mongo_repo.update_one(
                query={"file_id": file_id},
                update=update_data,
                collection_name=collection,
            )

            logging.info(
                f"[File Repo] [Soft Delete] Soft deleted {result} files(s): {file_id} in collection: {collection}"
            )
            logging.info(
                f"[File Repo] [Soft Delete] Delete operation completed successfully"
            )
            return result

        except Exception as e:
            logging.error(
                f"[File Repo] [Soft Delete] Error soft deleting files: {str(e)}"
            )
            logging.error(
                f"[File Repo] [Soft Delete] File ID: {file_id}, Deleted by: {deleted_by}, Collection: {collection_name}"
            )
            raise

    async def find_files_paginated(
        self,
        query_filter: Dict[str, Any],
        page: int = 1,
        page_size: int = 10,
        sort: Optional[Dict[str, Any]] = None,
        collection_name: str = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Find files with pagination
        """
        try:
            logging.info(
                f"[File Repo] [Find Paginated] Starting paginated files search"
            )
            logging.info(
                f"[File Repo] [Find Paginated] Search parameters - Page: {page}, Page Size: {page_size}"
            )
            logging.info(f"[File Repo] [Find Paginated] Query filter: {query_filter}")
            logging.info(f"[File Repo] [Find Paginated] Sort options: {sort}")

            # Use provided collection or default to file_metadata
            collection = collection_name or self.file_metadata_collection
            logging.info(f"[File Repo] [Find Paginated] Using collection: {collection}")

            files, total = await self.mongo_repo.find_many_paginated(
                query=query_filter,
                page=page,
                page_size=page_size,
                sort=sort,
                collection_name=collection,
            )

            logging.info(f"[File Repo] [Find Paginated] Search completed successfully")
            logging.info(
                f"[File Repo] [Find Paginated] Found {len(files)} files out of {total} total in collection: {collection}"
            )
            logging.info(
                f"[File Repo] [Find Paginated] Current page: {page}, Page size: {page_size}"
            )

            # Log files details for debugging
            if files:
                logging.info(f"[File Repo] [Find Paginated] Sample files found:")
                for i, file_doc in enumerate(files[:3]):  # Log first 3 files
                    file_id = file_doc.get("file_id")
                    file_name = file_doc.get("file_name")
                    file_type = file_doc.get("file_type")
                    status = file_doc.get("status")
                    logging.info(
                        f"[File Repo] [Find Paginated] File {i + 1}: ID={file_id}, Name={file_name}, Type={file_type}, Status={status}"
                    )

            return files, total

        except Exception as e:
            logging.error(
                f"[File Repo] [Find Paginated] Error in paginated search: {str(e)}"
            )
            logging.error(f"[File Repo] [Find Paginated] Query filter: {query_filter}")
            logging.error(
                f"[File Repo] [Find Paginated] Page: {page}, Page size: {page_size}, Collection: {collection_name}"
            )
            raise

    async def delete_file(self, file_id: str, collection_name: str = None) -> int:
        """
        Hard delete a file from the collection
        """
        try:
            logging.info(f"[File Repo] [Delete File] Starting hard delete operation")
            logging.info(f"[File Repo] [Delete File] File ID: {file_id}")

            # Use provided collection or default to files_storage
            collection = collection_name or self.files_storage_collection
            logging.info(f"[File Repo] [Delete File] Using collection: {collection}")

            result = await self.mongo_repo.delete_one(
                query={"file_id": file_id}, collection_name=collection
            )

            logging.info(
                f"[File Repo] [Delete File] Hard deleted {result} file(s): {file_id} in collection: {collection}"
            )
            return result

        except Exception as e:
            logging.error(
                f"[File Repo] [Delete File] Error hard deleting file: {str(e)}"
            )
            logging.error(
                f"[File Repo] [Delete File] File ID: {file_id}, Collection: {collection_name}"
            )
            raise

    async def list_files_by_student(
        self, student_id: str, page: int, page_size: int
    ) -> FileListResponse:
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find({"student_id": student_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(page_size)
        )
        docs = [FileMetadataResponse(**d) async for d in cursor]
        total = await self.collection.count_documents({"student_id": student_id})
        return docs, total
