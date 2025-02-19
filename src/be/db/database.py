import os
from typing import List
import iso639  # You'll need to add this to your dependencies

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from db.models import Base, Article, Language, ArticleKeyword, Paragraph

# from logger_config import logger
from loguru import logger
from models.responses import Keyword
from alembic import command
from alembic.config import Config

load_dotenv()

DB_USER = os.getenv("AI_ART_DB_USER")
DB_PASSWORD = os.getenv("AI_ART_DB_PASSWORD")
DB_HOST = os.getenv("AI_ART_DB_HOST")
DB_PORT = os.getenv("AI_ART_DB_PORT")
DB_NAME = os.getenv("AI_ART_DB_NAME")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)
session = Session()


def upgrade_database_to_latest():
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        logger.error(f"Error upgrading database: {e}")


def get_iso_languages() -> List[tuple]:
    """Get a list of ISO language codes and names"""
    languages = []
    for lang in iso639.data:
        # Get the language entry
        logger.debug(lang)
        languages.append((lang["iso639_1"], lang["name"]))

    return languages


async def init_languages():
    """Initialize the languages table with ISO language codes if empty"""
    try:
        with Session() as session:
            # Check if languages table is empty
            language_count = session.query(Language).count()

            if language_count == 0:
                logger.info("Languages table is empty. Populating with ISO languages...")

                # Get ISO languages
                iso_languages = get_iso_languages()

                # Insert languages in batches
                batch_size = 100
                for i in range(0, len(iso_languages), batch_size):
                    logger.info(f"Inserting batch {i} of {len(iso_languages)}")
                    batch = iso_languages[i : i + batch_size]
                    languages = [Language(code=code, name=name) for code, name in batch]
                    session.bulk_save_objects(languages)
                    session.commit()

                logger.info(f"Successfully added {len(iso_languages)} languages to the database")
            else:
                logger.info(f"Languages table already contains {language_count} entries")

    except Exception as e:
        logger.error(f"Error initializing languages: {e}")
        raise


async def init_db():
    if not database_exists(engine.url):
        try:
            create_database(engine.url)
            logger.info(f"Created database: {engine.url}")
        except Exception as e:
            logger.error(f"Error creating database: {e}")
    else:
        logger.info(f"Database already exists: {engine.url}")

    logger.info("Creating tables in the database")
    Base.metadata.create_all(bind=engine)

    # Add language initialization
    await init_languages()

    upgrade_database_to_latest()


def insert_article(title: str, content: str, lang: str) -> Article:
    lang_id = session.query(Language).filter(Language.code == lang).first().id

    item = Article(title=title, content=content, lang_id=lang_id)
    session.add(item)
    session.commit()

    return item


def insert_paragraph(content: str, idx: int, article_id: str) -> Article:
    item = Paragraph(content=content, order=idx, article_id=article_id)
    session.add(item)
    session.commit()

    return item


def insert_keyword(keyword: str, lang: str) -> Keyword:
    lang_id = session.query(Language).filter(Language.code == lang).first().id

    item = Keyword(keyword=keyword, lang_id=lang_id)
    session.add(item)
    session.commit()

    return item


def insert_keyword_article(keyword_id: int, article_id: int):
    item = ArticleKeyword(keyword_id=keyword_id, article_id=article_id)
    session.add(item)
    session.commit()
