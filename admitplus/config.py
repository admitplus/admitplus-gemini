import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # Text models
    OPENAI_TEXT_MODEL_DEFAULT: str = os.getenv("OPENAI_TEXT_MODEL_DEFAULT", "")
    OPENAI_TEXT_MODEL: str = os.getenv("OPENAI_TEXT_MODEL", "")
    OPENAI_TEXT_MODEL_CHEAP: str = os.getenv("OPENAI_TEXT_MODEL_CHEAP", "")
    OPENAI_TEXT_MODEL_HEAVY: str = os.getenv("OPENAI_TEXT_MODEL_HEAVY", "")
    OPENAI_TEXT_MODEL_EVAL: str = os.getenv("OPENAI_TEXT_MODEL_EVAL", "")
    # Embedding models
    OPENAI_EMBED_MODEL_DEFAULT: str = os.getenv("OPENAI_EMBED_MODEL_DEFAULT", "")
    # Image models
    OPENAI_IMAGE_MODEL_DEFAULT: str = os.getenv("OPENAI_IMAGE_MODEL_DEFAULT", "")
    # TTS models
    OPENAI_TTS_MODEL_DEFAULT: str = os.getenv("OPENAI_TTS_MODEL_DEFAULT", "")

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Text models
    GEMINI_TEXT_MODEL_DEFAULT: str = os.getenv("GEMINI_TEXT_MODEL_DEFAULT", "")
    GEMINI_TEXT_MODEL_HEAVY: str = os.getenv("GEMINI_TEXT_MODEL_HEAVY", "")
    # Embedding
    GEMINI_EMBED_MODEL_DEFAULT: str = os.getenv("GEMINI_EMBED_MODEL_DEFAULT", "")
    # Image
    GEMINI_IMAGE_MODEL_DEFAULT: str = os.getenv("GEMINI_IMAGE_MODEL_DEFAULT", "")

    # MongoDB Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    # Databases
    MONGO_APPLICATION_WAREHOUSE_DB_NAME: str = os.getenv(
        "MONGO_APPLICATION_WAREHOUSE_DB_NAME", ""
    )
    MONGO_UNIVERSITY_WAREHOUSE_DB_NAME: str = os.getenv(
        "MONGO_UNIVERSITY_WAREHOUSE_DB_NAME", ""
    )

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "") or "0")
    REDIS_USERNAME: str = os.getenv("REDIS_USERNAME", "")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB_NUM: int = int(os.getenv("REDIS_DB_NUM", "") or "0")

    # Vector DB (Milvus)
    MILVUS_URI: str = os.getenv("MILVUS_URI", "")
    MILVUS_USER_NAME: str = os.getenv("MILVUS_USER_NAME", "")
    MILVUS_PASSWORD: str = os.getenv("MILVUS_PASSWORD", "")
    MILVUS_API_KEY: str = os.getenv("MILVUS_API_KEY", "")

    MILVUS_IELTS_WRITING_PROMPTS_COLLECTION: str = os.getenv(
        "MILVUS_IELTS_WRITING_PROMPTS_COLLECTION", ""
    )
    MILVUS_IELTS_WRITING_SAMPLES_COLLECTION: str = os.getenv(
        "MILVUS_IELTS_WRITING_SAMPLES_COLLECTION", ""
    )
    MILVUS_IELTS_WRITING_KNOWLEDGE_COLLECTION: str = os.getenv(
        "MILVUS_IELTS_WRITING_KNOWLEDGE_COLLECTION", ""
    )

    # Storage (Google Cloud Storage)
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
    CDN_BASE_URL: str = os.getenv("CDN_BASE_URL", "")

    # Email / Zoho Configuration
    RESET_PASSWORD_VERIFICATION_EMAIL: str = os.getenv(
        "RESET_PASSWORD_VERIFICATION_EMAIL", ""
    )
    SIGN_UP_VERIFICATION_EMAIL: str = os.getenv("SIGN_UP_VERIFICATION_EMAIL", "")
    ZOHO_APP_PASSWORD: str = os.getenv("ZOHO_APP_PASSWORD", "")
    ZOHO_EMAIL: str = os.getenv("ZOHO_EMAIL", "")

    # JWT / Auth Configuration
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "") or "0"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "") or "0"
    )
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")

    # MongoDB Collections - Core Business
    # User & Agency
    USER_PROFILES_COLLECTION: str = os.getenv("USER_PROFILES_COLLECTION", "")
    USER_AVATARS_COLLECTION: str = os.getenv("USER_AVATARS_COLLECTION", "")

    # Agencies
    AGENCY_PROFILES_COLLECTION: str = os.getenv("AGENCY_PROFILES_COLLECTION", "")
    AGENCY_MEMBERS_COLLECTION: str = os.getenv("AGENCY_MEMBERS_COLLECTION", "")

    # Teachers
    TEACHER_PROFILES_COLLECTION: str = os.getenv("TEACHER_PROFILES_COLLECTION", "")

    # Students
    STUDENT_PROFILES_COLLECTION: str = os.getenv("STUDENT_PROFILES_COLLECTION", "")
    STUDENT_APPLICATIONS_COLLECTION: str = os.getenv(
        "STUDENT_APPLICATIONS_COLLECTION", ""
    )
    STUDENT_ASSIGNMENTS_COLLECTION: str = os.getenv(
        "STUDENT_ASSIGNMENTS_COLLECTION", ""
    )
    STUDENT_HIGHLIGHTS_COLLECTION: str = os.getenv("STUDENT_HIGHLIGHTS_COLLECTION", "")

    # Applications
    APPLICATION_DOCUMENTS_COLLECTION: str = os.getenv(
        "APPLICATION_DOCUMENTS_COLLECTION", ""
    )

    # Essay
    ESSAY_COLLECTION: str = os.getenv("ESSAY_COLLECTION", "")
    ESSAY_DRAFTS_COLLECTION: str = os.getenv("ESSAY_DRAFTS_COLLECTION", "")
    ESSAY_RECORDS_COLLECTION: str = os.getenv("ESSAY_RECORDS_COLLECTION", "")
    ESSAY_CONVERSATIONS_COLLECTION: str = os.getenv(
        "ESSAY_CONVERSATIONS_COLLECTION", ""
    )
    ESSAY_QUESTIONS_COLLECTION: str = os.getenv("ESSAY_QUESTIONS_COLLECTION", "")
    # File
    FILE_METADATA_COLLECTION: str = os.getenv("FILE_METADATA_COLLECTION", "")
    FILES_STORAGE_COLLECTION: str = os.getenv("FILE_STORAGE_COLLECTION", "")

    # Invitations
    INVITATIONS_COLLECTION: str = os.getenv("INVITATIONS_COLLECTION", "")

    # Matching
    MATCHING_REPORTS_COLLECTION: str = os.getenv("MATCHING_REPORTS_COLLECTION", "")

    # University Warehouse
    UNIVERSITY_PROFILES_COLLECTION: str = os.getenv(
        "UNIVERSITY_PROFILES_COLLECTION", ""
    )
    UNIVERSITY_PROGRAMS_COLLECTION: str = os.getenv(
        "UNIVERSITY_PROGRAMS_COLLECTION", ""
    )
    UNIVERSITY_SCHOOLS_COLLECTION: str = os.getenv("UNIVERSITY_SCHOOLS_COLLECTION", "")
    UNIVERSITY_TUITION_COLLECTION: str = os.getenv("UNIVERSITY_TUITION_COLLECTION", "")

    RANKING_SNAPSHOTS_COLLECTION: str = os.getenv("RANKING_SNAPSHOTS_COLLECTION", "")
    ADMISSION_CYCLES_COLLECTION: str = os.getenv("ADMISSION_CYCLES_COLLECTION", "")
    ADMISSION_REQUIREMENTS_COLLECTION: str = os.getenv(
        "ADMISSION_REQUIREMENTS_COLLECTION", ""
    )
    ADMISSION_OUTCOMES_COLLECTION: str = os.getenv("ADMISSION_OUTCOMES_COLLECTION", "")
    ADMISSION_STATES_COLLECTION: str = os.getenv("ADMISSION_STATES_COLLECTION", "")

    # Exams
    EXAM_TASKS_COLLECTION: str = os.getenv("EXAM_TASKS_COLLECTION", "")
    EXAM_ATTEMPTS_COLLECTION: str = os.getenv("EXAM_ATTEMPTS_COLLECTION", "")
    EXAM_FEEDBACKS_COLLECTION: str = os.getenv("EXAM_FEEDBACKS_COLLECTION", "")
    EXAM_MODEL_ESSAYS_COLLECTION: str = os.getenv("EXAM_MODEL_ESSAYS_COLLECTION", "")

    # Surveys & Feedback
    SURVEY_QUESTIONS_COLLECTION: str = os.getenv("SURVEY_QUESTIONS_COLLECTION", "")
    SURVEY_ANSWERS_COLLECTION: str = os.getenv("SURVEY_ANSWERS_COLLECTION", "")
    FEATURE_EVENTS_COLLECTION: str = os.getenv("FEATURE_EVENTS_COLLECTION", "")
    FEEDBACKS_COLLECTION: str = os.getenv("FEEDBACKS_COLLECTION", "")

    # System Configuration
    HOURS_24: int = int(os.getenv("HOURS_24", "") or "0")
    MAX_ATTEMPTS_PER_24H: int = int(os.getenv("MAX_ATTEMPTS_PER_24H", "") or "0")
    DEFAULT_TRIAL_DAYS: int = int(os.getenv("DEFAULT_TRIAL_DAYS", "") or "0")

    # User Roles
    USER_ROLE_ADMIN: str = os.getenv("USER_ROLE_ADMIN", "")
    USER_ROLE_AGENCY_ADMIN: str = os.getenv("USER_ROLE_AGENCY_ADMIN", "")
    USER_ROLE_AGENCY_MEMBER: str = os.getenv("USER_ROLE_AGENCY_MEMBER", "")
    USER_ROLE_COUNSELORS: str = os.getenv("USER_ROLE_COUNSELORS", "")
    USER_ROLE_TEACHER: str = os.getenv("USER_ROLE_TEACHER", "")
    USER_ROLE_STUDENT: str = os.getenv("USER_ROLE_STUDENT", "")
    USER_ROLE_AGENCY_STUDENT: str = os.getenv("USER_ROLE_AGENCY_STUDENT", "")

    # Upload Limits
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "") or "0")

    # Feishu Webhook Configuration
    FEISHU_WEBHOOK_URL: str = os.getenv("FEISHU_WEBHOOK_URL", "")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields instead of raising validation errors


settings = Settings()
