import logging
import traceback
from datetime import datetime
from typing import Dict, Any

try:
    from google.cloud import storage as gcs_storage

    GCS_AVAILABLE = True
except ImportError:
    gcs_storage = None
    GCS_AVAILABLE = False

from fastapi import HTTPException

from admitplus.config import settings
from admitplus.api.student.repos.student_file_repo import StudentFileRepo
from admitplus.api.files.file_service import FileService
from admitplus.api.files.file_schema import (
    FileAnalyzeRequest,
    FileAnalyzeResultResponse,
    FileParseStatus,
)
from admitplus.api.student.schemas.student_file_schema import (
    StudentFileResponse,
    StudentFileListResponse,
    StudentFileAttachRequest,
)
from admitplus.api.files.file_service import FileService
from admitplus.api.student.student_service import StudentService
from admitplus.api.student.highlights.student_highlight_service import (
    StudentHighlightService,
)
from admitplus.api.analysis.analyze_service import AnalysisService


class StudentFileService:
    def __init__(self):
        self.student_file_repo = StudentFileRepo()
        self.file_service = FileService()
        self.student_service = StudentService()
        self.highlight_service = StudentHighlightService()
        self.analyze_service = AnalysisService()

    def _doc_to_student_file_response(self, doc: Dict[str, Any]) -> StudentFileResponse:
        """
        Convert MongoDB document to StudentFileResponse
        """
        # Convert timestamps
        created_at = doc.get("created_at")
        if isinstance(created_at, (int, float)):
            created_at_dt = datetime.fromtimestamp(created_at)
        elif isinstance(created_at, datetime):
            created_at_dt = created_at
        else:
            created_at_dt = datetime.utcnow()

        updated_at = doc.get("updated_at", doc.get("created_at"))
        if isinstance(updated_at, (int, float)):
            updated_at_dt = datetime.fromtimestamp(updated_at)
        elif isinstance(updated_at, datetime):
            updated_at_dt = updated_at
        else:
            updated_at_dt = created_at_dt

        # Get parse_status
        parse_status_str = doc.get("parse_status", FileParseStatus.pending.value)
        try:
            parse_status = FileParseStatus(parse_status_str)
        except ValueError:
            parse_status = FileParseStatus.pending

        return StudentFileResponse(
            file_id=doc["file_id"],
            student_id=doc["student_id"],
            uploader_member_id=doc.get("uploader_member_id", ""),
            file_type=doc["file_type"],
            original_filename=doc.get("original_filename", doc.get("file_name", "")),
            storage_path=doc.get("storage_path", ""),
            mime_type=doc.get("mime_type", doc.get("content_type", "")),
            size_bytes=int(doc.get("size_bytes", doc.get("size", 0))),
            parse_status=parse_status,
            parsed_text=doc.get("parsed_text"),
            created_at=created_at_dt,
            updated_at=updated_at_dt,
        )

    async def attach_file_to_student(
        self,
        student_id: str,
        request: StudentFileAttachRequest,
        current_member_id: str,
    ) -> StudentFileResponse:
        """
        Attach a file to a student
        The file must already exist in files_storage collection (uploaded via /files/upload)
        """
        try:
            logging.info(
                f"[Student File Service] [Attach File] Attaching file {request.file_id} to student {student_id}"
            )

            # 1. Read file metadata from files_storage collection
            file_storage_doc = await self.student_file_repo.find_file_storage_by_id(
                request.file_id
            )

            if not file_storage_doc:
                logging.error(
                    f"[Student File Service] [Attach File] File {request.file_id} not found in files_storage"
                )
                raise HTTPException(
                    status_code=404, detail=f"File {request.file_id} not found"
                )

            logging.info(
                f"[Student File Service] [Attach File] Found file in files_storage: {request.file_id}"
            )

            # 2. Check if file is already attached to this student
            existing_doc = (
                await self.student_file_repo.find_file_metadata_by_student_and_file(
                    student_id=student_id, file_id=request.file_id
                )
            )

            if existing_doc:
                logging.warning(
                    f"[Student File Service] [Attach File] File {request.file_id} already attached to student {student_id}"
                )
                return self._doc_to_student_file_response(existing_doc)

            # 3. Create student file document in file_metadata collection
            created_at_ts = datetime.utcnow()
            student_file_doc = {
                "file_id": request.file_id,
                "student_id": student_id,
                "uploader_member_id": current_member_id,
                "file_type": request.file_type.value,
                "original_filename": file_storage_doc.get(
                    "file_name", file_storage_doc.get("original_filename", "")
                ),
                "storage_path": file_storage_doc.get("storage_path", ""),
                "mime_type": file_storage_doc.get(
                    "mime_type", file_storage_doc.get("content_type", "")
                ),
                "size_bytes": file_storage_doc.get(
                    "size_bytes", file_storage_doc.get("size", 0)
                ),
                "parse_status": FileParseStatus.pending.value,
                "parsed_text": None,
                "created_at": created_at_ts,
                "updated_at": created_at_ts,
                "deleted": False,
            }

            logging.info(
                f"[Student File Service] [Attach File] Creating student file document in file_metadata"
            )
            insert_id = await self.student_file_repo.insert_file_metadata(
                student_file_doc
            )

            if not insert_id:
                logging.error(
                    f"[Student File Service] [Attach File] Failed to insert file metadata"
                )
                raise HTTPException(
                    status_code=500, detail="Failed to create file metadata"
                )

            logging.info(
                f"[Student File Service] [Attach File] Successfully attached file {request.file_id} to student {student_id}"
            )

            # Return the created document
            return self._doc_to_student_file_response(student_file_doc)

        except Exception as e:
            logging.error(
                f"[Student File Service] [Attach File] Error attaching file: {str(e)}"
            )
            logging.error(
                f"[Student File Service] [Attach File] Traceback: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to attach file to student: {str(e)}"
            )

    async def list_student_files(
        self,
        student_id: str,
        page: int,
        page_size: int,
        current_member_id: str,
    ) -> StudentFileListResponse:
        """
        List all files for a student with pagination
        """
        try:
            logging.info(
                f"[Student File Service] [List Student Files] Listing files for student {student_id}, page {page}, page_size {page_size}"
            )

            files, total = await self.student_file_repo.find_student_files_paginated(
                student_id=student_id, page=page, page_size=page_size
            )

            # Convert documents to StudentFileResponse
            file_list = [self._doc_to_student_file_response(doc) for doc in files]

            has_next = (page * page_size) < total
            has_prev = page > 1

            logging.info(
                f"[Student File Service] [List Student Files] Found {len(file_list)} files out of {total} total"
            )

            return StudentFileListResponse(
                file_list=file_list,
                total=total,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_prev=has_prev,
            )

        except Exception as e:
            logging.error(
                f"[Student File Service] [List Student Files] Error listing files: {str(e)}"
            )
            logging.error(
                f"[Student File Service] [List Student Files] Traceback: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to list student files: {str(e)}"
            )

    async def get_file_metadata(
        self,
        file_id: str,
        current_member_id: str,
    ) -> StudentFileResponse:
        """
        Get file metadata by file_id
        """
        try:
            logging.info(
                f"[Student File Service] [Get File Metadata] Getting file metadata for {file_id}"
            )

            file_doc = await self.student_file_repo.find_file_metadata_by_id(file_id)

            if not file_doc:
                logging.warning(
                    f"[Student File Service] [Get File Metadata] File {file_id} not found"
                )
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")

            logging.info(
                f"[Student File Service] [Get File Metadata] Found file metadata for {file_id}"
            )
            return self._doc_to_student_file_response(file_doc)

        except Exception as e:
            logging.error(
                f"[Student File Service] [Get File Metadata] Error getting file metadata: {str(e)}"
            )
            logging.error(
                f"[Student File Service] [Get File Metadata] Traceback: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to get file metadata: {str(e)}"
            )

    async def delete_student_file(
        self,
        file_id: str,
        current_member_id: str,
    ) -> StudentFileResponse:
        """
        Delete a student file (from file_metadata, files_storage, and GCS)
        """
        try:
            logging.info(
                f"[Student File Service] [Delete File] Deleting file {file_id}"
            )

            # 1. Find file in file_metadata to get storage_path
            file_meta_doc = await self.student_file_repo.find_file_metadata_by_id(
                file_id
            )

            if not file_meta_doc:
                logging.warning(
                    f"[Student File Service] [Delete File] File {file_id} not found in file_metadata"
                )
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")

            storage_path = file_meta_doc.get("storage_path")

            # 2. Delete from file_metadata collection
            deleted_count = await self.student_file_repo.delete_file_metadata(file_id)
            logging.info(
                f"[Student File Service] [Delete File] Deleted {deleted_count} document(s) from file_metadata"
            )

            # 3. Delete from files_storage collection
            deleted_storage_count = await self.student_file_repo.delete_file_storage(
                file_id
            )
            logging.info(
                f"[Student File Service] [Delete File] Deleted {deleted_storage_count} document(s) from files_storage"
            )

            # 4. Delete from GCS (if storage_path exists)
            if storage_path and GCS_AVAILABLE:
                try:
                    credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
                    if credentials_path:
                        storage_client = gcs_storage.Client.from_service_account_json(
                            credentials_path
                        )
                    else:
                        storage_client = gcs_storage.Client()

                    bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
                    blob = bucket.blob(storage_path)

                    if blob.exists():
                        blob.delete()
                        logging.info(
                            f"[Student File Service] [Delete File] Deleted file from GCS: {storage_path}"
                        )
                    else:
                        logging.warning(
                            f"[Student File Service] [Delete File] File does not exist in GCS: {storage_path}"
                        )
                except Exception as gcs_error:
                    logging.error(
                        f"[Student File Service] [Delete File] Failed to delete from GCS: {str(gcs_error)}"
                    )
                    # Continue even if GCS deletion fails

            logging.info(
                f"[Student File Service] [Delete File] Successfully deleted file {file_id}"
            )

            # Return the deleted file metadata
            return self._doc_to_student_file_response(file_meta_doc)

        except Exception as e:
            logging.error(
                f"[Student File Service] [Delete File] Error deleting file: {str(e)}"
            )
            logging.error(
                f"[Student File Service] [Delete File] Traceback: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to delete file: {str(e)}"
            )

    async def analyze_student_file(
        self,
        file_id: str,
        current_member_id: str,
    ) -> FileAnalyzeResultResponse:
        """
        Analyze a student file and create highlights
        """
        try:
            logging.info(
                f"[Student File Service] [Analyze File] Analyzing file {file_id}"
            )

            # 1. 拿 metadata + 权限校验
            file_meta = await self.file_service.get_file_metadata(file_id)
            if not file_meta:
                logging.error(
                    f"[Student File Service] [Analyze File] File {file_id} not found"
                )
                raise HTTPException(status_code=404, detail=f"File {file_id} not found")

            if not file_meta.student_id:
                logging.error(
                    f"[Student File Service] [Analyze File] File {file_id} has no student_id"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file_id} is not associated with a student",
                )

            await self.student_service.ensure_member_can_access_student(
                student_id=file_meta.student_id,
                member_id=current_member_id,
            )

            # 2. 调用 analyze_service 解析文件（从 storage 读文件，调用 LLM）
            (
                parsed_text,
                student_profile_data,
                highlight_items,
            ) = await self.analyze_service.analyze_student_file(
                file_metadata=file_meta,
                mode="standard",
            )

            # 3. 更新 file_metadata.parse_status / parsed_text
            await self.file_service.update_file_parse_result(
                file_id=file_id,
                parsed_text=parsed_text,
                status=FileParseStatus.parsed.value,
            )

            # 4. 更新 student_profile（如果提取到了学生信息）
            updated_student_profile = None
            if student_profile_data:
                try:
                    logging.info(
                        f"[Student File Service] [Analyze File] Updating student profile for student {file_meta.student_id}"
                    )
                    updated_student_profile = (
                        await self.student_service.update_student_profile(
                            student_id=file_meta.student_id,
                            student_profile_data=student_profile_data,
                        )
                    )
                    logging.info(
                        f"[Student File Service] [Analyze File] Successfully updated student profile"
                    )
                except Exception as e:
                    logging.warning(
                        f"[Student File Service] [Analyze File] Failed to update student profile: {str(e)}"
                    )
                    # Continue even if profile update fails

            # 5. 基于解析结果批量创建 student_highlights
            highlights_created = 0
            if highlight_items:
                highlights_created = (
                    await self.highlight_service.create_highlights_from_parsed_result(
                        student_id=file_meta.student_id,
                        items=highlight_items,
                        created_by_member_id=current_member_id,
                        source_id=file_id,
                        source_type="file_analysis",
                    )
                )
                logging.info(
                    f"[Student File Service] [Analyze File] Created {highlights_created} highlights"
                )

            # 6. 返回 summary（包含学生信息和highlights）
            logging.info(
                f"[Student File Service] [Analyze File] Successfully analyzed file {file_id}"
            )

            # Convert student profile to dict if available
            student_profile_dict = None
            if updated_student_profile:
                if hasattr(updated_student_profile, "model_dump"):
                    student_profile_dict = updated_student_profile.model_dump()
                elif hasattr(updated_student_profile, "dict"):
                    student_profile_dict = updated_student_profile.dict()
                else:
                    student_profile_dict = updated_student_profile

            return FileAnalyzeResultResponse(
                file_id=file_id,
                parse_status=FileParseStatus.parsed,
                extracted_text_length=len(parsed_text or ""),
                new_highlights_created=highlights_created,
                student_profile=student_profile_dict,
                highlights=[
                    item for item in highlight_items[:10]
                ],  # Return first 10 highlights
            )

        except HTTPException:
            raise
        except Exception as e:
            logging.error(
                f"[Student File Service] [Analyze File] Error analyzing file: {str(e)}"
            )
            logging.error(
                f"[Student File Service] [Analyze File] Traceback: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to analyze file: {str(e)}"
            )
