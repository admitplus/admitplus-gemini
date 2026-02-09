from typing import List

from pydantic import BaseModel


class UniversitySuggestionsRequest(BaseModel):
    country_code: str


class UniversitySuggestionItem(BaseModel):
    university_name: str
    logo_url: str = ""


class UniversitySuggestionsResponse(BaseModel):
    suggestions: List[UniversitySuggestionItem]


class ProgramSuggestionsResponse(BaseModel):
    suggestions: List[str]
