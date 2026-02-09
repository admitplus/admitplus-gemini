from enum import Enum
from typing import Dict


class ExamEnum(str, Enum):
    IELTS = "ielts"
    TOEFL = "toefl"
    SAT = "sat"


class ExamSectionEnum(str, Enum):
    WRITING = "writing"
    SPEAKING = "speaking"
    READING = "reading"
    LISTENING = "listening"


class TaskTypeEnum(str, Enum):
    TASK1 = "task1"
    TASK2 = "task2"
    PART1 = "part1"
    PART2 = "part2"
    PART3 = "part3"


class SeriesEnum(str, Enum):
    s15 = "15"
    s16 = "16"
    s17 = "17"
    s18 = "18"
    s19 = "19"


class AttemptModeEnum(str, Enum):
    PRACTICE = "practice"
    EXAM = "exam"


class FeedbackTypeEnum(str, Enum):
    AI = "ai"
    MANUAL = "manual"


class ScoreScaleEnum(str, Enum):
    IELTS_WRITING_BAND_0_9_V1 = "ielts_writing_band_0_9_v1"
    IELTS_SPEAKING_BAND_0_9_V1 = "ielts_speaking_band_0_9_v1"
    TOEFL_WRITING_SCORE_0_30_V1 = "toefl_writing_score_0_30_v1"
    TOEFL_SPEAKING_SCORE_0_30_V1 = "toefl_speaking_score_0_30_v1"


# Score range constants
IELTS_SCORE_MIN = 0.0
IELTS_SCORE_MAX = 9.0
IELTS_SCORE_INCREMENT = 0.5

TOEFL_SCORE_MIN = 0.0
TOEFL_SCORE_MAX = 30.0
TOEFL_SCORE_INCREMENT = 1.0


SCORE_SCALE_MAPPING: Dict[str, str] = {
    "ielts.writing": ScoreScaleEnum.IELTS_WRITING_BAND_0_9_V1,
    "ielts.speaking": ScoreScaleEnum.IELTS_SPEAKING_BAND_0_9_V1,
    "toefl.writing": ScoreScaleEnum.TOEFL_WRITING_SCORE_0_30_V1,
    "toefl.speaking": ScoreScaleEnum.TOEFL_SPEAKING_SCORE_0_30_V1,
}

SCORE_SCALE_VERSION = "v1"

FALLBACK_FORMAT_MAP: Dict[str, str] = {
    ExamEnum.IELTS: "band_0_9",
    ExamEnum.TOEFL: "score_0_30",
}


def get_score_scale(exam: str, section: str) -> str:
    exam_lower, section_lower = exam.lower(), section.lower()
    key = f"{exam_lower}.{section_lower}"

    return SCORE_SCALE_MAPPING.get(key) or (
        f"{exam_lower}_{section_lower}_{FALLBACK_FORMAT_MAP.get(exam_lower)}_{SCORE_SCALE_VERSION}"
    )


__all__ = [
    "ExamEnum",
    "SeriesEnum",
    "ExamSectionEnum",
    "TaskTypeEnum",
    "AttemptModeEnum",
    "FeedbackTypeEnum",
    "ScoreScaleEnum",
    "IELTS_SCORE_MIN",
    "IELTS_SCORE_MAX",
    "IELTS_SCORE_INCREMENT",
    "TOEFL_SCORE_MIN",
    "TOEFL_SCORE_MAX",
    "TOEFL_SCORE_INCREMENT",
    "get_score_scale",
]
