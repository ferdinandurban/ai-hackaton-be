from http import HTTPStatus
import os
from loguru import logger
from ai.openai_assistant import (
    command,
    create_assistant,
    generate_image,
    list_assistants,
    retrieve_assistant,
    upload_file_to_s3,
)
import openai
from fastapi import APIRouter, Depends, HTTPException


from models.requests import PromptRequest
import sys

openai.api_key = os.getenv("OPENAI_API_KEY")
logger.add(sys.stderr, format="{time} {level} {message}", filter="openai_router", level="INFO")
openai_router = APIRouter()


@openai_router.get("/assistant/list")
async def get_list_assistants():
    try:
        assistants = list_assistants()
        return assistants
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@openai_router.get("/assistant/last")
async def get_last_assistants():
    try:
        response = retrieve_assistant()
        return response
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@openai_router.post("/assistant/create")
async def post_create_assistant():
    try:
        response = create_assistant()

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@openai_router.post("/command")
async def post_command(request: PromptRequest):
    try:
        logger.info(f"Command: {request.topic}")
        response = command(topic=request.topic)
        logger.info(f"Command finished. Response: {response}")

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@openai_router.post("/image/generate")
async def post_image_generate(request: PromptRequest):
    try:
        response = generate_image(prompt=request.topic, client=None, short_id="dummy_image")

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


@openai_router.post("/image/upload")
async def upload_image(request: str):
    try:
        response = upload_file_to_s3(request)

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


# TODO dodelat posilani obrazku do s3
# NOTE: parsovanni zprav by melo byt hotove
