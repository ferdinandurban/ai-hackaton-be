from datetime import datetime
from http import HTTPStatus
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models.responses as responses
from db.models import Article, Language, ArticleKeyword, Keyword
from db.dependencies import get_db

articles_router = APIRouter()


@articles_router.get("/homepage", response_model=List[responses.Article])
async def get_homepage(
    lang: str = "en", keyword: Optional[str] = None, db: Session = Depends(get_db)
):
    language_id = db.query(Language).filter_by(code=lang).first().id
    result = []

    if keyword is None:
        articles = db.query(Article).filter_by(lang_id=language_id).all()

        for article in articles:
            keywords_ids = db.query(ArticleKeyword).filter_by(article_id=article.id).all()

            keywords = (
                db.query(Keyword)
                .filter(Keyword.id.in_([keyword.keyword_id for keyword in keywords_ids]))
                .all()
            )

            d = responses.ArticleData(
                title=article.title,
                perex="",
                keywords=[keyword.keyword for keyword in keywords],
                paragraphs=[paragraph.content for paragraph in article.paragraphs],
            )
            a = responses.Article(
                publicId=article.short_id,
                imageUrl=article.image_url,
                lang=lang,
                seoSlug=article.seo_slug,
                url=f"/{lang}/{article.short_id}/{article.seo_slug}",
                data=d,
            )

            result.append(a)

        return result

    keyword_articles = db.query(ArticleKeyword).filter(ArticleKeyword.keyword_id == keyword).all()
    articles = []

    for keyword_article in keyword_articles:
        article = db.query(Article).filter(Article.id == keyword_article.article_id).first()
        articles.append(article)

    return result


@articles_router.get("/{public_id}", response_model=responses.Article)
async def get_article(public_id: str, lang: str = "en", db: Session = Depends(get_db)):
    try:
        article = db.query(Article).filter_by(short_id=public_id).first()
        article.visited += 1
        article.last_visit = datetime.now()
        db.commit()

        lang = db.query(Language).filter_by(id=article.lang_id).first().code

        keywords_ids = db.query(ArticleKeyword).filter_by(article_id=article.id).all()

        keywords = (
            db.query(Keyword)
            .filter(Keyword.id.in_([keyword.keyword_id for keyword in keywords_ids]))
            .all()
        )

        d = responses.ArticleData(
            title=article.title,
            perex="",
            keywords=[keyword.keyword for keyword in keywords],
            paragraphs=[paragraph.content for paragraph in article.paragraphs],
        )
        return responses.Article(
            publicId=article.short_id,
            imageUrl=article.image_url,
            lang=lang,
            seoSlug=article.seo_slug,
            url=f"/{lang}/{article.short_id}/{article.seo_slug}",
            data=d,
        )

    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Article not found")


@articles_router.get("/keywords", response_model=List[responses.Keyword])
async def get_keywords(lang: str = "en", db: Session = Depends(get_db)):
    language_id = db.query(Language).filter(Language.code == lang).first().id

    return db.query(Keyword).filter(Keyword.lang_id == language_id).all()
