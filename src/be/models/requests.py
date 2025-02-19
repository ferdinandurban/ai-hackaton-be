from typing import List

from pydantic import BaseModel


class PromptRequest(BaseModel):
    topic: str


class ArticleData(BaseModel):
    lang: str
    title: str
    intro: str
    paragraphs: List[str]
    keywords: List[str]
    imagePrompt: str
    social: str
