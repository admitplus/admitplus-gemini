import logging
import traceback
import time
from datetime import datetime, timedelta
from typing import Optional

try:
    from google.cloud import storage as gcs_storage
    from google.auth.exceptions import TransportError
    import requests
    from requests.exceptions import SSLError as RequestsSSLError
    import urllib3.exceptions

    GCS_AVAILABLE = True
except ImportError:
    gcs_storage = None
    GCS_AVAILABLE = False

from admitplus.config import settings
from .file_metadata_repo import FileRepo
from .file_schema import (
    FileListRequest,
    FileListResponse,
    FileMetadata,
    FileStatus,
    FileStorageInfoResponse,
    FileType,
    FileUploadResponse,
)
from admitplus.common.response_schema import OperationSuccessResponse
from admitplus.utils.crypto_utils import generate_uuid


class FileService:
    def __init__(self):
        if not GCS_AVAILABLE:
            raise ImportError(
                "Google Cloud Storage library not found. "
                "Please install it with: pip install google-cloud-storage"
            )

        self.bucket_name = settings.GCS_BUCKET_NAME
        self.cdn_base_url = settings.CDN_BASE_URL

        # Initialize GCS client with credentials
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        if credentials_path:
            logging.info(
                f"[File Service] [Init] Using GCS credentials from: {credentials_path}"
            )
            try:
                self._storage_client = gcs_storage.Client.from_service_account_json(
                    credentials_path
                )
            except Exception as e:
                logging.error(
                    f"[File Service] [Init] Failed to load GCS credentials from {credentials_path}: {e}"
                )
                raise
        else:
            logging.warning(
                "[File Service] [Init] GOOGLE_APPLICATION_CREDENTIALS not set, using default credentials"
            )
            self._storage_client = gcs_storage.Client()

        # Initialize repository
        self.file_repo = FileRepo()

    def _public_url(self, blob_path: str) -> str:
        if self.cdn_base_url:
            return f"{self.cdn_base_url.rstrip('/')}/{blob_path}"
        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_path}"

    def _upload_with_retry(
        self, blob, file_content: bytes, content_type: str, max_retries: int = 5
    ):
        """
        Upload file to GCS with retry logic for SSL errors
        """
        last_exception = None
        for attempt in range(max_retries):
            try:
                blob.upload_from_string(file_content, content_type=content_type)
                return  # Success
            except (TransportError, RequestsSSLError, urllib3.exceptions.SSLError) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s, 8s
                    logging.warning(
                        f"[File Service] [Upload Retry] SSL error on attempt {attempt + 1}/{max_retries}: {e}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logging.error(
                        f"[File Service] [Upload Retry] SSL error after {max_retries} attempts: {e}"
                    )
            except Exception as e:
                # For non-SSL errors, don't retry
                logging.error(
                    f"[File Service] [Upload Retry] Non-SSL error during upload: {e}"
                )
                raise

        # If we get here, all retries failed
        raise last_exception

    def _create_document_metadata(self, doc: dict) -> FileMetadata:
        """
        Safely create FileMetadata from MongoDB document
        Handles field name variations between files_storage and file_metadata collections
        """
        try:
            # Validate required fields with fallbacks for field name variations
            file_id = doc.get("file_id")
            if not file_id:
                raise ValueError("Missing required field: file_id")

            # Handle file_name variations: file_name or original_filename
            file_name = doc.get("file_name") or doc.get("original_filename")
            if not file_name:
                raise ValueError(
                    "Missing required field: file_name (or original_filename)"
                )

            # Handle content_type variations: content_type or mime_type
            content_type = doc.get("content_type") or doc.get("mime_type")
            if not content_type:
                raise ValueError("Missing required field: content_type (or mime_type)")

            # Handle size variations: size or size_bytes
            size = doc.get("size") or doc.get("size_bytes")
            if size is None:
                raise ValueError("Missing required field: size (or size_bytes)")

            # Validate other required fields
            if "file_type" not in doc:
                raise ValueError("Missing required field: file_type")
            if "status" not in doc:
                raise ValueError("Missing required field: status")
            if "created_at" not in doc:
                raise ValueError("Missing required field: created_at")
            if "storage_path" not in doc:
                raise ValueError("Missing required field: storage_path")

            # Handle uploaded_by - may be missing in some collections, use empty string as fallback
            uploaded_by = doc.get("uploaded_by") or doc.get("uploader_member_id") or ""

            # Convert timestamp safely
            created_at = doc["created_at"]
            if isinstance(created_at, (int, float)):
                created_at_dt = datetime.fromtimestamp(created_at)
            elif isinstance(created_at, datetime):
                created_at_dt = created_at
            else:
                raise ValueError(f"Invalid created_at type: {type(created_at)}")

            # Convert verified_at if present
            verified_at_dt = None
            if doc.get("verified_at"):
                verified_at = doc["verified_at"]
                if isinstance(verified_at, (int, float)):
                    verified_at_dt = datetime.fromtimestamp(verified_at)
                elif isinstance(verified_at, datetime):
                    verified_at_dt = verified_at

            return FileMetadata(
                file_id=file_id,
                file_name=file_name,
                content_type=content_type,
                size=int(size),  # Ensure integer
                file_type=doc["file_type"],  # FileType will validate this
                student_id=doc.get("student_id"),
                application_id=doc.get("application_id"),
                agency_id=doc.get("agency_id"),
                description=doc.get("description"),
                status=doc["status"],
                created_at=created_at_dt,
                uploaded_by=uploaded_by,
                storage_path=doc["storage_path"],
                file_url=self._public_url(doc["storage_path"]),
                verified_by=doc.get("verified_by"),
                verified_at=verified_at_dt,
            )
        except Exception as e:
            logging.error(
                f"[File Service] [Create Document Metadata] Failed to create FileMetadata: {e}"
            )
            raise ValueError(f"Invalid document data: {e}")

    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        content_type: str,
        file_type: FileType,
        uploaded_by: str,
        student_id: str = None,
        application_id: str = None,
        agency_id: str = None,
        description: str = None,
    ) -> FileUploadResponse:
        """
        File upload: upload files directly to GCS and store metadata in MongoDB
        """
        logging.info(f"[File Service] [File Upload] Starting upload for {file_name}")
        logging.info(
            f"[File Service] [File Upload] Upload parameters - User: {uploaded_by}, Type: {file_type}, "
            f"Student: {student_id}, Application: {application_id}, Agency: {agency_id}"
        )

        try:
            # Validate files size (max 50MB)
            file_size = len(file_content)
            max_size = settings.MAX_FILE_SIZE  # 50MB
            logging.info(
                f"[File Service] [File Upload] File size: {file_size} bytes (max: {max_size} bytes)"
            )

            if file_size > max_size:
                logging.error(
                    f"[File Service] [File Upload] File size {file_size} bytes exceeds maximum allowed size of {max_size} bytes"
                )
                raise ValueError(
                    f"File size {file_size} bytes exceeds maximum allowed size of {max_size} bytes"
                )

            # Validate files name
            if not file_name or len(file_name.strip()) == 0:
                logging.error(
                    f"[File Service] [File Upload] File name validation failed: '{file_name}'"
                )
                raise ValueError("File name cannot be empty")

            # Validate content type
            if not content_type or len(content_type.strip()) == 0:
                logging.error(
                    f"[File Service] [File Upload] Content type validation failed: '{content_type}'"
                )
                raise ValueError("Content type cannot be empty")

            logging.info(
                f"[File Service] [File Upload] Validation passed, proceeding with upload"
            )

            # Generate unique files ID
            file_id = generate_uuid()
            logging.info(f"[File Service] [File Upload] Generated files ID: {file_id}")

            # Generate storage path
            safe_name = file_name.replace("/", "_").replace("\\", "_")
            ts = int(datetime.utcnow().timestamp())
            blob_path = f"files/{file_id}/{ts}-{safe_name}"
            logging.info(
                f"[File Service] [File Upload] Generated storage path: {blob_path}"
            )

            # Upload files to GCS
            logging.info(
                f"[File Service] [File Upload] Starting GCS upload to bucket: {self.bucket_name}"
            )
            bucket = self._storage_client.bucket(self.bucket_name)
            blob = bucket.blob(blob_path)

            # Set content type
            blob.content_type = content_type
            logging.info(
                f"[File Service] [File Upload] Set blob content type: {content_type}"
            )

            # Upload files content with retry logic for SSL errors
            self._upload_with_retry(blob, file_content, content_type)
            logging.info(f"[File Service] [File Upload] Successfully uploaded to GCS")

            # Create files record in database (using files_storage collection)
            created_at_ts = datetime.utcnow()
            file_doc = {
                "file_id": file_id,
                "file_name": file_name,
                "content_type": content_type,
                "mime_type": content_type,  # Alias for API compatibility
                "size": file_size,
                "size_bytes": file_size,  # Alias for API compatibility
                "file_type": file_type,
                "student_id": student_id,
                "application_id": application_id,
                "agency_id": agency_id,
                "description": description,
                "storage_path": blob_path,
                "bucket": self.bucket_name,
                "status": "active",  # Direct upload is immediately active
                "created_at": created_at_ts,
                "updated_at": created_at_ts,
                "uploaded_at": created_at_ts,
                "uploaded_by": uploaded_by,
                "deleted": False,
            }

            logging.info(
                f"[File Service] [File Upload] Creating database record for files {file_id}"
            )
            # Insert files record into files_storage collection
            insert_id = await self.file_repo.insert_file(
                file_doc, collection_name=self.file_repo.files_storage_collection
            )
            logging.info(f"[File Service] [File Upload] Inserted {insert_id}")

            logging.info(
                f"[File Service] [File Upload] Successfully uploaded files {file_id}"
            )

            return FileUploadResponse(
                file_id=file_id,
                storage_path=blob_path,
                original_filename=file_name,
                mime_type=content_type,
                size_bytes=file_size,
                created_at=created_at_ts,
            )

        except Exception as e:
            logging.error(
                f"[File Service] [File Upload] Failed to upload files: {str(e)}"
            )
            raise

    async def get_file_info(self, file_id: str) -> Optional[FileStorageInfoResponse]:
        """
        Get file storage info by file ID (from files_storage collection)
        """
        logging.info(
            f"[File Service] [Get File Info] Getting storage info for file {file_id}"
        )

        try:
            # Find file from files_storage collection (exclude soft-deleted ones)
            logging.info(
                f"[File Service] [Get File Info] Querying database for file {file_id}"
            )
            file_doc = await self.file_repo.find_file_by_id(
                file_id, collection_name=self.file_repo.files_storage_collection
            )

            if not file_doc:
                logging.warning(
                    f"[File Service] [Get File Info] File {file_id} not found in database"
                )
                return None

            logging.info(
                f"[File Service] [Get File Info] Found file document for {file_id}"
            )
            logging.info(
                f"[File Service] [Get File Info] File document keys: {list(file_doc.keys())}"
            )

            # Convert timestamps
            created_at = file_doc.get("created_at")
            if isinstance(created_at, (int, float)):
                created_at_dt = datetime.fromtimestamp(created_at)
            elif isinstance(created_at, datetime):
                created_at_dt = created_at
            else:
                raise ValueError(f"Invalid created_at type: {type(created_at)}")

            updated_at = file_doc.get("updated_at", file_doc.get("created_at"))
            if isinstance(updated_at, (int, float)):
                updated_at_dt = datetime.fromtimestamp(updated_at)
            elif isinstance(updated_at, datetime):
                updated_at_dt = updated_at
            else:
                updated_at_dt = created_at_dt

            # Convert to FileStorageInfoResponse
            logging.info(
                f"[File Service] [Get File Info] Converting document to FileStorageInfoResponse for file {file_id}"
            )
            info = FileStorageInfoResponse(
                file_id=file_doc["file_id"],
                storage_path=file_doc["storage_path"],
                bucket=file_doc.get("bucket", self.bucket_name),
                mime_type=file_doc.get("mime_type", file_doc.get("content_type", "")),
                size_bytes=int(file_doc.get("size_bytes", file_doc.get("size", 0))),
                status=FileStatus(file_doc["status"]),
                created_at=created_at_dt,
                updated_at=updated_at_dt,
            )

            logging.info(
                f"[File Service] [Get File Info] Successfully retrieved storage info for file {file_id}"
            )
            logging.info(
                f"[File Service] [Get File Info] File details - Name: {file_doc.get('file_name')}, Size: {info.size_bytes}, Status: {info.status}"
            )
            return info

        except Exception as e:
            logging.error(
                f"[File Service] [Get File Info] Failed to get storage info for file {file_id}: {str(e)}"
            )
            logging.error(
                f"[File Service] [Get File Info] Error details: {traceback.format_exc()}"
            )
            raise

    async def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """
        Get files metadata by files ID (legacy method, kept for backward compatibility)
        Tries files_storage collection first, then falls back to file_metadata collection
        """
        logging.info(
            f"[File Service] [Get File Metadata] Getting metadata for files {file_id}"
        )

        try:
            # First, try to find file in files_storage collection (has file_name field)
            logging.info(
                f"[File Service] [Get File Metadata] Querying files_storage collection for files {file_id}"
            )
            file_doc = await self.file_repo.find_file_by_id(
                file_id, collection_name=self.file_repo.files_storage_collection
            )

            # If not found in files_storage, try file_metadata collection (has original_filename field)
            if not file_doc:
                logging.info(
                    f"[File Service] [Get File Metadata] File {file_id} not found in files_storage, trying file_metadata collection"
                )
                file_doc = await self.file_repo.find_file_by_id(
                    file_id, collection_name=self.file_repo.file_metadata_collection
                )

            if not file_doc:
                logging.warning(
                    f"[File Service] [Get File Metadata] File {file_id} not found in database"
                )
                return None

            logging.info(
                f"[File Service] [Get File Metadata] Found files document for {file_id}"
            )
            logging.info(
                f"[File Service] [Get File Metadata] File document keys: {list(file_doc.keys())}"
            )

            # Convert to FileMetadata (handles field name variations)
            logging.info(
                f"[File Service] [Get File Metadata] Converting document to FileMetadata for files {file_id}"
            )
            metadata = self._create_document_metadata(file_doc)

            logging.info(
                f"[File Service] [Get File Metadata] Successfully retrieved metadata for files {file_id}"
            )
            logging.info(
                f"[File Service] [Get File Metadata] Metadata details - Name: {metadata.file_name}, Size: {metadata.size}, Type: {metadata.file_type}, Status: {metadata.status}"
            )
            return metadata

        except Exception as e:
            logging.error(
                f"[File Service] [Get File Metadata] Failed to get metadata for files {file_id}: {str(e)}"
            )
            logging.error(
                f"[File Service] [Get File Metadata] Error details: {traceback.format_exc()}"
            )
            raise

    async def delete_file(self, file_id: str, deleted_by: str) -> bool:
        """
        Hard delete a file: delete GCS blob and MongoDB document from files_storage collection
        """
        logging.info(
            f"[File Service] [Delete File] Hard deleting file {file_id} by user {deleted_by}"
        )

        try:
            # Find existing file from files_storage collection
            logging.info(
                f"[File Service] [Delete File] Querying database for file {file_id}"
            )
            file_doc = await self.file_repo.find_file_by_id(
                file_id, collection_name=self.file_repo.files_storage_collection
            )

            if not file_doc:
                logging.warning(
                    f"[File Service] [Delete File] File {file_id} not found in database"
                )
                return False

            logging.info(
                f"[File Service] [Delete File] Found file document for {file_id}"
            )
            logging.info(
                f"[File Service] [Delete File] File details before deletion - Name: {file_doc.get('file_name')}, Size: {file_doc.get('size_bytes', file_doc.get('size'))}, Status: {file_doc.get('status')}"
            )

            # Get storage path
            storage_path = file_doc.get("storage_path")
            if not storage_path:
                logging.error(
                    f"[File Service] [Delete File] File {file_id} has no storage_path, cannot delete from GCS"
                )
                return False

            # Delete from GCS
            try:
                logging.info(
                    f"[File Service] [Delete File] Deleting file from GCS at path: {storage_path}"
                )
                bucket = self._storage_client.bucket(self.bucket_name)
                blob = bucket.blob(storage_path)

                if blob.exists():
                    blob.delete()
                    logging.info(
                        f"[File Service] [Delete File] Successfully deleted file from GCS: {storage_path}"
                    )
                else:
                    logging.warning(
                        f"[File Service] [Delete File] File does not exist in GCS at path: {storage_path}"
                    )
            except Exception as e:
                logging.error(
                    f"[File Service] [Delete File] Failed to delete file from GCS: {str(e)}"
                )
                # Continue with MongoDB deletion even if GCS deletion fails

            # Delete from MongoDB (files_storage collection)
            logging.info(
                f"[File Service] [Delete File] Deleting file document from MongoDB"
            )
            deleted_count = await self.file_repo.delete_file(
                file_id, collection_name=self.file_repo.files_storage_collection
            )

            if deleted_count > 0:
                logging.info(
                    f"[File Service] [Delete File] Successfully deleted file {file_id} from MongoDB"
                )
            else:
                logging.warning(
                    f"[File Service] [Delete File] No document deleted for file_id: {file_id}"
                )

            logging.info(
                f"[File Service] [Delete File] Successfully hard deleted file {file_id} by user {deleted_by}"
            )
            return deleted_count > 0

        except Exception as e:
            logging.error(
                f"[File Service] [Delete File] Failed to delete file {file_id} by user {deleted_by}: {str(e)}"
            )
            logging.error(
                f"[File Service] [Delete File] Error details: {traceback.format_exc()}"
            )
            raise

    async def generate_download_url(self, file_id: str) -> Optional[str]:
        """
        Generate presigned URL for download
        """
        logging.info(
            f"[File Service] [Generate Download URL] Generating download URL for files {file_id}"
        )

        try:
            # Find files from files_storage collection (exclude soft-deleted ones)
            logging.info(
                f"[File Service] [Generate Download URL] Querying database for files {file_id}"
            )
            file_doc = await self.file_repo.find_file_by_id(
                file_id, collection_name=self.file_repo.files_storage_collection
            )

            if not file_doc:
                logging.warning(
                    f"[File Service] [Generate Download URL] File {file_id} not found in database"
                )
                return None

            logging.info(
                f"[File Service] [Generate Download URL] Found files document for {file_id}"
            )
            logging.info(
                f"[File Service] [Generate Download URL] File details - Name: {file_doc.get('file_name')}, Status: {file_doc.get('status')}, Storage Path: {file_doc.get('storage_path')}"
            )

            # Check if files is in a valid state for download
            if file_doc["status"] != "active":
                logging.warning(
                    f"[File Service] [Generate Download URL] File {file_id} is not active (status: {file_doc['status']}), cannot generate download URL"
                )
                return None

            # Get storage path
            storage_path = file_doc["storage_path"]
            logging.info(
                f"[File Service] [Generate Download URL] Using storage path: {storage_path}"
            )

            # Try to generate presigned URL, fallback to public URL if not possible
            try:
                logging.info(
                    f"[File Service] [Generate Download URL] Attempting to generate presigned URL for files {file_id}"
                )
                bucket = self._storage_client.bucket(self.bucket_name)
                blob = bucket.blob(storage_path)

                # Generate presigned URL (expires in 1 hour)
                expires_at = datetime.utcnow() + timedelta(hours=1)
                logging.info(
                    f"[File Service] [Generate Download URL] Presigned URL will expire at: {expires_at}"
                )

                presigned_url = blob.generate_signed_url(
                    version="v4", expiration=expires_at, method="GET"
                )

                logging.info(
                    f"[File Service] [Generate Download URL] Successfully generated presigned download URL for files {file_id}"
                )
                logging.info(
                    f"[File Service] [Generate Download URL] Presigned URL length: {len(presigned_url)} characters"
                )
                return presigned_url

            except Exception as e:
                # Fallback to public URL if presigned URL generation fails
                logging.warning(
                    f"[File Service] [Generate Download URL] Failed to generate presigned URL for files {file_id}: {e}"
                )
                logging.info(
                    f"[File Service] [Generate Download URL] Using public URL as fallback for files {file_id}"
                )
                public_url = self._public_url(storage_path)
                logging.info(
                    f"[File Service] [Generate Download URL] Generated public URL: {public_url}"
                )
                return public_url

        except Exception as e:
            logging.error(
                f"[File Service] [Generate Download URL] Failed to generate download URL for files {file_id}: {str(e)}"
            )
            logging.error(
                f"[File Service] [Generate Download URL] Error details: {traceback.format_exc()}"
            )
            raise

    async def list_files(self, request: FileListRequest) -> FileListResponse:
        """
        List files with pagination and filtering
        """
        logging.info(f"[File Service] [List Files] Listing files with filters")

        try:
            # Build query filter
            query_filter = {"deleted": {"$ne": True}}

            # Apply filters from request
            if request.student_id and request.student_id.strip():
                query_filter["student_id"] = request.student_id.strip()

            if request.file_type:
                query_filter["file_type"] = request.file_type

            if request.application_id and request.application_id.strip():
                query_filter["application_id"] = request.application_id.strip()

            if request.agency_id and request.agency_id.strip():
                query_filter["agency_id"] = request.agency_id.strip()

            # Find files with pagination using find_many_paginated
            files, total = await self.file_repo.find_files_paginated(
                query_filter=query_filter,
                page=request.page,
                page_size=request.page_size,
            )

            # Convert to FileMetadata list
            result = []
            for doc in files:
                try:
                    metadata = self._create_document_metadata(doc)
                    result.append(metadata)
                except ValueError as e:
                    logging.warning(
                        f"[File Service] [List Files] Skipping invalid document: {e}"
                    )
                    continue

            has_next = (
                (request.page - 1) * request.page_size + request.page_size
            ) < total

            logging.info(
                f"[File Service] [List Files] Successfully retrieved {len(result)} files"
            )

            return FileListResponse(
                files=result,
                total=total,
                page=request.page,
                page_size=request.page_size,
                has_next=has_next,
            )

        except Exception as e:
            logging.error(f"[File Service] [List Files] Failed to list files: {str(e)}")
            raise

    async def download_file_to_memory(self, file_id: str) -> Optional[bytes]:
        """
        下载文件到内存中，返回文件内容的字节数据
        主要用于PDF、DOC等文档文件的文本提取
        """
        logging.info(
            f"[File Service] [Download File To Memory] Downloading files {file_id} to memory"
        )

        try:
            # 查找文件元数据（排除已软删除的文件）
            logging.info(
                f"[File Service] [Download File To Memory] Querying database for files {file_id}"
            )
            file_doc = await self.file_repo.find_file_by_id(
                file_id, collection_name=self.file_repo.files_storage_collection
            )

            if not file_doc:
                logging.warning(
                    f"[File Service] [Download File To Memory] File {file_id} not found in database"
                )
                return None

            logging.info(
                f"[File Service] [Download File To Memory] Found files document for {file_id}"
            )
            logging.info(
                f"[File Service] [Download File To Memory] File details - Name: {file_doc.get('file_name')}, "
                f"Content Type: {file_doc.get('content_type')}, Size: {file_doc.get('size')}"
            )

            # 检查文件状态是否有效
            if file_doc["status"] != "active":
                logging.warning(
                    f"[File Service] [Download File To Memory] File {file_id} is not active "
                    f"(status: {file_doc['status']}), cannot download"
                )
                return None

            # 获取存储路径
            storage_path = file_doc["storage_path"]
            logging.info(
                f"[File Service] [Download File To Memory] Using storage path: {storage_path}"
            )

            # 从GCS下载文件内容
            logging.info(
                f"[File Service] [Download File To Memory] Starting download from GCS for files {file_id}"
            )
            bucket = self._storage_client.bucket(self.bucket_name)
            blob = bucket.blob(storage_path)

            # 检查文件是否存在
            if not blob.exists():
                logging.error(
                    f"[File Service] [Download File To Memory] File {file_id} not found in GCS at path: {storage_path}"
                )
                return None

            # 下载文件内容到内存
            logging.info(
                f"[File Service] [Download File To Memory] Downloading files content to memory"
            )
            file_content = blob.download_as_bytes()

            # 验证下载的内容大小
            downloaded_size = len(file_content)
            expected_size = file_doc.get("size", 0)
            logging.info(
                f"[File Service] [Download File To Memory] Download completed - "
                f"Downloaded size: {downloaded_size} bytes, Expected size: {expected_size} bytes"
            )

            if expected_size > 0 and downloaded_size != expected_size:
                logging.warning(
                    f"[File Service] [Download File To Memory] File size mismatch for {file_id}. "
                    f"Expected: {expected_size}, Downloaded: {downloaded_size}"
                )

            logging.info(
                f"[File Service] [Download File To Memory] Successfully downloaded files {file_id} to memory"
            )
            return file_content

        except Exception as e:
            logging.error(
                f"[File Service] [Download File To Memory] Failed to download files {file_id} to memory: {str(e)}"
            )
            logging.error(
                f"[File Service] [Download File To Memory] Error details: {traceback.format_exc()}"
            )
            return None

    async def download_file_to_disk(self, file_id: str, local_file_path: str) -> bool:
        """
        下载文件到本地磁盘
        """
        logging.info(
            f"[File Service] [Download File To Disk] Downloading files {file_id} to {local_file_path}"
        )

        try:
            # 查找文件元数据
            file_doc = await self.file_repo.find_file_by_id(
                file_id, collection_name=self.file_repo.files_storage_collection
            )

            if not file_doc:
                logging.warning(
                    f"[File Service] [Download File To Disk] File {file_id} not found in database"
                )
                return False

            # 检查文件状态
            if file_doc["status"] != "active":
                logging.warning(
                    f"[File Service] [Download File To Disk] File {file_id} is not active "
                    f"(status: {file_doc['status']}), cannot download"
                )
                return False

            # 获取存储路径
            storage_path = file_doc["storage_path"]

            # 从GCS下载文件到本地
            bucket = self._storage_client.bucket(self.bucket_name)
            blob = bucket.blob(storage_path)

            # 检查文件是否存在
            if not blob.exists():
                logging.error(
                    f"[File Service] [Download File To Disk] File {file_id} not found in GCS at path: {storage_path}"
                )
                return False

            # 下载到本地文件
            logging.info(
                f"[File Service] [Download File To Disk] Downloading files to disk: {local_file_path}"
            )
            blob.download_to_filename(local_file_path)

            # 验证文件是否成功下载
            import os

            if os.path.exists(local_file_path):
                file_size = os.path.getsize(local_file_path)
                logging.info(
                    f"[File Service] [Download File To Disk] Successfully downloaded files {file_id} to "
                    f"{local_file_path} (size: {file_size} bytes)"
                )
                return True
            else:
                logging.error(
                    f"[File Service] [Download File To Disk] Failed to download files {file_id} - "
                    f"local files not created: {local_file_path}"
                )
                return False

        except Exception as e:
            logging.error(
                f"[File Service] [Download File To Disk] Failed to download files {file_id} to disk: {str(e)}"
            )
            logging.error(
                f"[File Service] [Download File To Disk] Error details: {traceback.format_exc()}"
            )
            return False

    async def update_file_parse_result(
        self, file_id: str, parsed_text: Optional[str] = None, status: str = "parsed"
    ) -> bool:
        """
        Update file parse result (parse_status and parsed_text)
        """
        logging.info(
            f"[File Service] [Update File Parse Result] Updating parse result for file: {file_id}, status: {status}"
        )

        try:
            update_data = {
                "$set": {"parse_status": status, "parsed_at": datetime.utcnow()}
            }

            if parsed_text is not None:
                update_data["$set"]["parsed_text"] = parsed_text

            logging.info(
                f"[File Service] [Update File Parse Result] Update data: {update_data}"
            )

            result = await self.file_repo.mongo_repo.update_one(
                query={"file_id": file_id},
                update=update_data,
                collection_name=self.file_repo.file_metadata_collection,
            )

            if result > 0:
                logging.info(
                    f"[File Service] [Update File Parse Result] Successfully updated parse result for file: {file_id}"
                )
            else:
                logging.warning(
                    f"[File Service] [Update File Parse Result] No file updated for file_id: {file_id}"
                )

            return result > 0

        except Exception as e:
            logging.error(
                f"[File Service] [Update File Parse Result] Error updating parse result for file {file_id}: {str(e)}"
            )
            logging.error(
                f"[File Service] [Update File Parse Result] Error details: {traceback.format_exc()}"
            )
            return False
