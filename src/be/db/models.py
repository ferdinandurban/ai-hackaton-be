import base64
from concurrent.futures import thread
import datetime
import re
import uuid

from sqlalchemy import Column, String, ForeignKey, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
    header = Column(String)
    title = Column(String)
    perex = Column(String)
    image_prompt = Column(String)
    image_url = Column(String)
    seo_slug = Column(String)
    visited = Column(Integer, default=0)
    last_visit = Column(DateTime(timezone=True))
    published = Column(DateTime(timezone=True), default=datetime.datetime.now())
    short_id = Column(String(8), unique=False, nullable=False)
    lang_id = Column(UUIDType(binary=True), ForeignKey("languages.id"))
    paragraphs = relationship("Paragraph", back_populates="article")
    note = Column(String)
    assistant_id = Column(UUIDType(binary=True), ForeignKey("openai_assistants.id"))
    thread_id = Column(String)
    twitter_text = Column(String)

    @staticmethod
    def create_short_id():
        return base64.b64encode(uuid.uuid4().bytes)[:8].decode("utf-8")

    @staticmethod
    def create_seo_slug(title: str):
        if title is None:
            return None
        slug = title.lower()
        slug = re.sub(r"\s+|-+", "-", slug)
        slug = re.sub(r"[^a-z0-9-]", "", slug)
        slug = slug.strip("-")
        return slug

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.short_id = self.create_short_id()
        self.seo_slug = self.create_seo_slug(self.title)


class Paragraph(Base):
    __tablename__ = "paragraphs"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
    content = Column(String)
    order = Column(Integer)
    article_id = Column(UUIDType(binary=True), ForeignKey("articles.id"))
    article = relationship("Article", back_populates="paragraphs")


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
    keyword = Column(String, unique=True, nullable=False)
    label = Column(String)
    lang_id = Column(UUIDType(binary=True), ForeignKey("languages.id"))
    article_id = Column(UUIDType(binary=True), ForeignKey("articles.id"))


class Language(Base):
    __tablename__ = "languages"

    id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
    code = Column(String)
    name = Column(String)


class ArticleKeyword(Base):
    __tablename__ = "article_keywords"

    article_id = Column(UUIDType(binary=True), ForeignKey("articles.id"), primary_key=True)
    keyword_id = Column(UUIDType(binary=True), ForeignKey("keywords.id"), primary_key=True)


class OpenAIAssistant(Base):
    __tablename__ = "openai_assistants"
    id = Column(UUIDType(binary=True), primary_key=True, default=uuid.uuid4)
    assistant_id = Column(String)
    instructions = Column(String)
    model = Column(String)
    description = Column(String)
    name = Column(String)
    datetime_created = Column(DateTime(timezone=True), default=datetime.datetime.now())
    datetime_updated = Column(DateTime(timezone=True), default=datetime.datetime.now())
