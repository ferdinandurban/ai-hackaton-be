FROM python:3.12-slim AS builder

# install PDM
RUN pip install -U pdm
# disable update check
ENV PDM_CHECK_UPDATE=false
# copy files
COPY pyproject.toml pdm.lock README.md /project/

# install dependencies and project into the local packages directory
WORKDIR /project
RUN pdm install --check --prod --no-editable

# run stage
FROM builder

WORKDIR /project
# retrieve packages from build stage
COPY --from=builder /project/.venv/ /project/.venv
ENV PATH="/project/.venv/bin:$PATH"
# set command/entrypoint, adapt to fit your needs
COPY src /project/src
COPY alembic /project/alembic
COPY alembic.ini /project/alembic.ini

EXPOSE 8000  
CMD ["uvicorn", "main:app", "--app-dir", "/project/src/be", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
