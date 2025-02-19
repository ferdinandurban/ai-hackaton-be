import datetime
from typing import List

from db import dependencies
from fastapi import APIRouter, Depends

import db.models as models
import models.requests as requests

from db.database import insert_keyword
from logger_config import logger

generator_router = APIRouter()


@generator_router.post("/article")
async def create_article(request: requests.ArticleData, db=Depends(dependencies.get_db)):
    try:
        lang_id = db.query(models.Language).filter(models.Language.code == request.lang).first().id

        article = models.Article(
            lang_id=lang_id, title=request.title, image_prompt=request.imagePrompt
        )
        article.published = datetime.datetime.now()

        db.add(article)
        db.commit()

        for keyword in request.keywords:
            k = db.query(models.Keyword.id).filter_by(keyword=keyword).first()

            if not k:
                k = models.Keyword(keyword=keyword, lang_id=lang_id)
                db.add(k)
                db.commit()

            db.add(models.ArticleKeyword(keyword_id=k.id, article_id=article.id))
            db.commit()

        for idx, paragraph in enumerate(request.paragraphs):
            db.add(models.Paragraph(content=paragraph, order=idx, article_id=article.id))
            db.commit()

        return {"response": article.short_id}

    except Exception as e:
        logger.error(e)


@generator_router.post("/keyword")
async def create_keyword(request: List[str], db=Depends(dependencies.get_db)):
    try:
        for keyword in request:
            response = insert_keyword(keyword=keyword, lang="cs")

        return {"response": response.id}
    except Exception as e:
        logger.error(e)


#
# @generator_router.post("/paragraph")
# async def create_paragraph(request: List[ParagraphRequest], db=Depends(dependencies.get_db)):
#     try:
#         for paragraph in request:
#             response = insert_article(title=article, content=article, lang="cs")
#
#         return {"response": response.id}
#     except Exception as e:
#         logger.error(e)
