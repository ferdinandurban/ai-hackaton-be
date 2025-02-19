# FastAPI Backend Service

A backend for generating articles + images based on request.

## Features

- FastAPI web framework
- PostgreSQL database with SQLAlchemy ORM
- Database migrations with Alembic
- OpenAI API integration
- Docker containerization
- Testing with pytest
- Code quality tools (ruff)
- Logging with loguru
- Error monitoring with Sentry

## Requirements

- Python 3.12
- PostgreSQL
- PDM (Python dependency manager)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pdm install
   ```
3. Set up environment variables in `.env`:

   ```
   # Database
   AI_ART_DB_USER=postgres
   AI_ART_DB_PASSWORD=postgres
   AI_ART_DB_HOST=localhost
   AI_ART_DB_PORT=5432
   AI_ART_DB_NAME=ai_articles

   # OpenAI
   OPENAI_API_KEY=your_openai_key
   AI_ART_OPENAI_PROJECT_API_KEY=your_project_key
   AI_ART_OPENAI_ORGANIZATION_ID=your_org_id
   AI_ART_OPENAI_PROJECT_ID=your_project_id
   AI_ART_OPENAI_ASSISTANT_ID=your_assistant_id

   # S3 Storage (Optional)
   AI_ART_S3_ACCESS_KEY_ID=your_s3_key
   AI_ART_S3_SECRET_ACCESS_KEY=your_s3_secret
   AI_ART_S3_ENDPOINT=https://fra1.digitaloceanspaces.com
   AI_ART_S3_REGION=fra1
   AI_ART_S3_BUCKET=your_bucket
   AI_ART_S3_IMAGE_FOLDER=ai_articles
   ```

## Development

Start the development server:

```bash
pdm run start
```

Run tests:

```bash
pdm run test
```

Run linting:

```bash
pdm run lint
```

Format code:

```bash
pdm run fmt
```

Run type checking:

```bash
pdm run mypy
```

## Docker Deployment

1. Build and run with Docker Compose:

   ```bash
   docker compose up -d
   ```

2. The API will be available at `http://localhost:8000`

## API Routes

- `/api/oai` - OpenAI integration endpoints
- `/api/articles` - Article management endpoints
- `/api/generate` - Data generation endpoints

## Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```
