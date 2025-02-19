from typing import List, Optional

from pydantic import BaseModel


class Keyword(BaseModel):
    key: str
    label: str


class ArticleData(BaseModel):
    title: str
    perex: Optional[str]
    keywords: List[str]
    paragraphs: List[str]


class Article(BaseModel):
    publicId: str
    imageUrl: Optional[str]
    lang: str
    seoSlug: str
    url: str
    data: ArticleData


class OAIArticleResponse(BaseModel):
    language: str
    title: str
    perex: str
    paragraphs: List[str]
    keywords: List[str]
    image_prompt: str
    twitter: str
