from typing import Literal, Optional, List

from pydantic import BaseModel


class University(BaseModel):
    university_id: int
    university_name: str


class UniversityList(BaseModel):
    universities: List[University]
