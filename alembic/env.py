import logging
from logging.config import fileConfig

from alembic import context

# from src.be.loguru_handler import LoguruHandler
from sqlalchemy import engine_from_config
from sqlalchemy import pool
import os
from loguru import logger
import sys

# Add this class to create a LoguruHandler
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Add this before config.set_main_option()
def setup_loguru():
    # Remove default alembic handlers
    logging.getLogger('alembic').handlers = []
    
    # Add loguru handler
    logging.getLogger('alembic').addHandler(InterceptHandler())
    
    # Set level
    logging.getLogger('alembic').setLevel(logging.DEBUG)
    
    # Add specific format for alembic logs
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>alembic</cyan> | <level>{message}</level>",
        filter=lambda record: "alembic" in record["extra"],
        level="DEBUG"
    )

# Add this call near the start of the script
setup_loguru()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

section = config.config_ini_section
config.set_section_option(section, "DB_USER", os.environ.get("AI_ART_DB_USER"))
config.set_section_option(section, "DB_PASSWORD", os.environ.get("AI_ART_DB_PASSWORD"))
config.set_section_option(section, "DB_HOST", os.environ.get("AI_ART_DB_HOST"))
config.set_section_option(section, "DB_PORT", os.environ.get("AI_ART_DB_PORT"))
config.set_section_option(section, "DB_NAME", os.environ.get("AI_ART_DB_NAME"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add LoguruHandler to the root logger
# logging.getLogger().handlers = [LoguruHandler()]

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
from src.be.db.models import Base

# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
