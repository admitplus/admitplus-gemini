from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator


class WritingStatus(str, Enum):
    """写作状态枚举"""

    DRAFT = "draft"  # 草稿
    SUCCESS = "success"  # 成功生成
    FAILED = "failed"  # 生成失败
    IN_PROGRESS = "in_progress"  # 生成中


class WriteSettings:
    """写作设置主类 - 包含所有相关的枚举和模型"""

    class ToneEnum(str, Enum):
        """文章语气枚举"""

        REFLECTIVE = "Reflective"
        INSPIRATIONAL = "Inspirational"
        ANALYTICAL = "Analytical"

    class NarrativePerspectiveEnum(str, Enum):
        """叙事视角枚举"""

        FIRST_PERSON = "First Person"
        THIRD_PERSON_LIMITED = "Third Person Limited"

    class LanguagePreferenceEnum(str, Enum):
        """语言偏好枚举"""

        AMERICAN_ENGLISH = "American English"
        BRITISH_ENGLISH = "British English"

    class StructureTemplateEnum(str, Enum):
        """结构模板枚举"""

        FIVE_PARAGRAPH = "5-Paragraph"
        STAR = "STAR"
        PROBLEM_GROWTH_REFLECTION = "Problem-Growth-Reflection"

    class GenerationGoalEnum(str, Enum):
        """生成目标枚举"""

        BRAINSTORM = "Brainstorm"
        OUTLINE = "Outline"
        FULL_DRAFT = "Full Draft"

    class LengthControlEnum(str, Enum):
        """长度控制枚举"""

        SHORT = "Short"
        MEDIUM = "Medium"
        LONG = "Long"
        CUSTOM = "Custom"

    class WriteTypeEnum(str, Enum):
        """写作类型枚举"""

        AUTO = "auto"  # 大模型自动生成
        MANUAL = "manual"  # 人工干预编写

    class Model(BaseModel):
        """写作设置模型"""

        tone: "WriteSettings.ToneEnum"
        narrative_perspective: "WriteSettings.NarrativePerspectiveEnum"
        language_preference: "WriteSettings.LanguagePreferenceEnum"
        structure_template: "WriteSettings.StructureTemplateEnum"
        generation_goal: "WriteSettings.GenerationGoalEnum"
        length_control: "WriteSettings.LengthControlEnum"
        custom_length: Optional[int] = None  # 当 length_control 为 Custom 时使用

        class Config:
            use_enum_values = True

    class Request(BaseModel):
        """写作设置请求模型"""

        tone: "WriteSettings.ToneEnum"
        narrative_perspective: "WriteSettings.NarrativePerspectiveEnum"
        language_preference: "WriteSettings.LanguagePreferenceEnum"
        structure_template: "WriteSettings.StructureTemplateEnum"
        generation_goal: "WriteSettings.GenerationGoalEnum"
        length_control: "WriteSettings.LengthControlEnum"
        custom_length: Optional[int] = None

        class Config:
            use_enum_values = True

    class Response(BaseModel):
        """写作设置响应模型"""

        tone: str
        narrative_perspective: str
        language_preference: str
        structure_template: str
        generation_goal: str
        length_control: str
        custom_length: Optional[int] = None
        created_at: Optional[datetime] = None
        updated_at: Optional[datetime] = None

    class Options(BaseModel):
        """写作设置选项配置模型 - 包含所有可选的枚举值"""

        tone: list[str]
        narrative_perspective: list[str]
        language_preference: list[str]
        structure_template: list[str]
        generation_goal: list[str]
        length_control: list[str]

        class Config:
            json_schema_extra = {
                "example": {
                    "tone": ["Reflective", "Inspirational", "Analytical"],
                    "narrative_perspective": ["First Person", "Third Person Limited"],
                    "language_preference": ["American English", "British English"],
                    "structure_template": [
                        "5-Paragraph",
                        "STAR",
                        "Problem-Growth-Reflection",
                    ],
                    "generation_goal": ["Brainstorm", "Outline", "Full Draft"],
                    "length_control": ["Short", "Medium", "Long", "Custom"],
                }
            }

    @classmethod
    def get_options(cls) -> Options:
        """获取所有写作设置选项"""
        return cls.Options(
            tone=[tone.value for tone in cls.ToneEnum],
            narrative_perspective=[
                perspective.value for perspective in cls.NarrativePerspectiveEnum
            ],
            language_preference=[
                language.value for language in cls.LanguagePreferenceEnum
            ],
            structure_template=[
                template.value for template in cls.StructureTemplateEnum
            ],
            generation_goal=[goal.value for goal in cls.GenerationGoalEnum],
            length_control=[length.value for length in cls.LengthControlEnum],
        )


class EssayRequirement(BaseModel):
    """文章要求模型 - 包含文章类型、提示文本和字数限制"""

    essay_type: Optional[str] = Field(
        None,
        description="文章类型，如：personal_statement, supplemental_essay, diversity_statement 等",
    )
    prompt_text: Optional[str] = Field(None, description="文章提示要求文本")
    word_limit: Optional[int] = Field(None, description="字数限制")

    class Config:
        json_schema_extra = {
            "example": {
                "essay_type": "personal_statement",
                "prompt_text": "Please write an essays that reflects your personal experiences, challenges, and goals.",
                "word_limit": 650,
            }
        }


class GenerateWriting:
    """写作生成主类 - 包含写作生成相关的所有模型"""

    class Request(BaseModel):
        """生成写作请求模型"""

        essay_id: Optional[str] = Field(
            None, description="文章ID。为None时表示新增文章，有值时表示修改现有文章"
        )
        materials: List[Dict[str, Any]] = Field(
            ...,
            description="学生材料数据列表[{'awards': 0}],key是achievements下的某个列表，值是index",
            min_items=1,
        )
        settings: WriteSettings.Model = Field(..., description="写作设置配置")
        type: WriteSettings.WriteTypeEnum = Field(
            default=WriteSettings.WriteTypeEnum.AUTO,
            description="写作类型：auto=AI生成，manual=人工编写",
        )
        manual_modify_content: Optional[str] = Field(
            None,
            description="手动修改的文章内容，当且仅当type=WriteSettings.WriteTypeEnum.MANUAL的时候有值",
        )
        essay_requirement: Optional[EssayRequirement] = Field(
            None,
            description="文章要求配置（可选），包含 essay_type, prompt_text, word_limit",
        )
        note: Optional[str] = Field(None, description="补充评论")
        essay_topic: Optional[str] = Field(None, description="文章主题（可选）")
        target_university: Optional[str] = Field(
            None, description="目标大学名称（可选）"
        )
        target_degree_level: Optional[str] = Field(
            None, description="目标学位级别（可选），如：Bachelor, Master, PhD"
        )
        target_major: Optional[str] = Field(None, description="目标专业（可选）")

        class Config:
            use_enum_values = True

    class Response(BaseModel):
        """生成写作响应模型"""

        writing_id: str = Field(..., description="生成的写作内容ID")
        content: str = Field(..., description="生成的写作内容")

        class Config:
            json_schema_extra = {
                "example": {
                    "writing_id": "writing_12345",
                    "content": "This is the generated essays content...",
                }
            }


# ==================== Writing Document Schemas ====================


class Writing(BaseModel):
    """写作文档模型 - 对应 MongoDB 中 writings_collection 的数据结构"""

    essay_id: str = Field(..., description="文章ID")
    user_id: str = Field(..., description="用户ID")
    file_id: str = Field(..., description="文件ID")
    materials: List[Dict[str, Any]] = Field(..., description="学生材料ID列表")
    settings: Dict[str, Any] = Field(..., description="写作设置配置")
    type: WriteSettings.WriteTypeEnum = Field(
        ..., description="写作类型：auto=AI生成，manual=人工编写"
    )
    content: str = Field(..., description="生成的文章内容")
    status: WritingStatus = Field(..., description="写作状态")

    # 可选字段
    essay_requirement: Optional[Dict[str, Any]] = Field(
        None, description="文章要求配置（essay_type, prompt_text, word_limit）"
    )
    essay_topic: Optional[str] = Field(None, description="文章主题")
    note: Optional[str] = Field(None, description="补充评论")  # 新增字段
    target_university: Optional[str] = Field(None, description="目标大学名称")
    target_degree_level: Optional[str] = Field(
        None, description="目标学位级别（Bachelor, Master, PhD）"
    )
    target_major: Optional[str] = Field(None, description="目标专业")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "essay_id": "essay_123456",
                "user_id": "user_789",
                "materials": ["material_001", "material_002"],
                "settings": {
                    "tone": "Reflective",
                    "narrative_perspective": "First Person",
                    "language_preference": "American English",
                    "structure_template": "5-Paragraph",
                    "generation_goal": "Full Draft",
                    "length_control": "Medium",
                },
                "type": "auto",
                "content": "This is my personal statement...",
                "status": "success",
                "essay_requirement": {
                    "essay_type": "personal_statement",
                    "prompt_text": "Tell us about yourself...",
                    "word_limit": 650,
                },
                "essay_topic": "Personal Growth",
                "target_university": "Stanford University",
                "target_degree_level": "Bachelor",
                "target_major": "Computer Science",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        }


class WritingResponse(BaseModel):
    """写作文档响应模型 - 用于 API 响应"""

    essay_id: str = Field(..., description="文章ID")
    user_id: str = Field(..., description="用户ID")
    materials: List[Dict[str, Any]] = Field(..., description="学生材料ID列表")
    settings: WriteSettings.Model = Field(..., description="写作设置配置")
    type: WriteSettings.WriteTypeEnum = Field(..., description="写作类型")
    content: str = Field(..., description="生成的文章内容")
    status: WritingStatus = Field(..., description="写作状态")

    # 可选字段
    essay_requirement: Optional[EssayRequirement] = Field(
        None, description="文章要求配置"
    )
    essay_topic: Optional[str] = Field(None, description="文章主题")
    target_university: Optional[str] = Field(None, description="目标大学名称")
    target_degree_level: Optional[str] = Field(None, description="目标学位级别")
    target_major: Optional[str] = Field(None, description="目标专业")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    id: Optional[str] = Field(None, alias="_id", exclude=True, description="MongoDB_ID")

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectId(cls, v):
        if v is not None and isinstance(v, ObjectId):
            return str(v)
        return v

    class Config:
        use_enum_values = True
        populate_by_name = True


class WritingListResponse(BaseModel):
    """写作列表响应模型"""

    writings: List[WritingResponse] = Field(..., description="写作列表")
    total: int = Field(..., description="总数")
    page: Optional[int] = Field(None, description="当前页码")
    page_size: Optional[int] = Field(None, description="每页数量")
    has_next: Optional[bool] = Field(None, description="是否有下一页")
    has_prev: Optional[bool] = Field(None, description="是否有上一页")
