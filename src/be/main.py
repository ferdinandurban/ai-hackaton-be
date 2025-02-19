from loguru_handler import LoguruHandler
from fastapi.concurrency import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI

from db.database import init_db
from db.dependencies import get_db

# from logger_config import logger
from loguru import logger
from routers.articles import articles_router
from routers.data_generator import generator_router
from routers.openai import openai_router
import logging
import sentry_sdk

sentry_sdk.init(
    dsn="https://a116b4a3853c4aada3ed14139cf09f41@o1233017.ingest.us.sentry.io/4504493795115008",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=1.0,
)
load_dotenv()


@asynccontextmanager
async def startup_event(app: FastAPI):
    setup_httpx_logging()
    setup_logging()

    logger.info("Starting up the FastAPI app")
    await init_db()
    logger.info("Server is running on http://0.0.0.0:8000")
    yield


def run():
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, workers=4)


if __name__ == "__main__":
    run()

app = FastAPI(lifespan=startup_event)

app.include_router(openai_router, prefix="/api/oai", tags=["openai"])
app.include_router(articles_router, prefix="/api/articles", tags=["articles"])
app.include_router(generator_router, prefix="/api/generate", tags=["generator"])


def setup_httpx_logging():
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.DEBUG)
    httpx_logger.handlers = [LoguruHandler()]


def setup_logging():
    logging.basicConfig(handlers=[LoguruHandler()], level=logging.INFO)

    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = [LoguruHandler()]

    for logger_name, logger_obj in logging.root.manager.loggerDict.items():
        if isinstance(logger_obj, logging.Logger):
            logger_obj.handlers = [LoguruHandler()]
