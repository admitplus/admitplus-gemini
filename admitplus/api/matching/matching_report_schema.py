from typing import List

from pydantic import BaseModel, Field


class MatchingReportRequest(BaseModel):
    university_ids: List[str] = Field(
        ..., min_length=1, max_length=5, description="List of universities IDs (1-5)"
    )
