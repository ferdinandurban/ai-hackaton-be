import threading
import time
import os
import uuid

from db.database import Session
from db.models import Article, Keyword, Language, OpenAIAssistant, Paragraph
from db.dependencies import SessionLocal
from dotenv import load_dotenv
from openai import Client, OpenAI
from openai.types.beta import Assistant
from openai.types.beta.threads import Message
import json
import requests
import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from loguru import logger
import sys

logger.add(sys.stderr, format="{time} {level} {message}", filter="openai_assistant", level="DEBUG")


load_dotenv(dotenv_path="../../.env")

OPENAI_API_KEY = os.environ.get("AI_ART_OPENAI_API_KEY", default="")
OPENAI_PROJECT_API_KEY = os.environ.get("AI_ART_OPENAI_PROJECT_API_KEY", default="")
OPENAI_ASSISTANT_ID = os.environ.get("AI_ART_OPENAI_ASSISTANT_ID", default="")
OPENAI_ORGANIZATION_ID = os.environ.get("AI_ART_OPENAI_ORGANIZATION_ID", default="")
OPENAI_PROJECT_ID = os.environ.get("AI_ART_OPENAI_PROJECT_ID", default="")
OPENAI_GPT_MODEL = os.environ.get("AI_ART_OPENAI_GPT_MODEL", default="gpt-4o")

AI_S3_SECRET_KEY = os.environ.get("AI_ART_S3_SECRET_ACCESS_KEY", default="")
AI_S3_ACCESS_KEY = os.environ.get("AI_ART_S3_ACCESS_KEY_ID", default="")
AI_S3_ENDPOINT = os.environ.get("AI_ART_S3_ENDPOINT")
AI_S3_REGION = os.environ.get("AI_ART_S3_REGION")
AI_S3_BUCKET = os.environ.get("AI_ART_S3_BUCKET")
AI_S3_IMAGE_FOLDER = os.environ.get("AI_ART_S3_IMAGE_FOLDER")

# logger.debug(f"{OPENAI_API_KEY=}")
# logger.debug(f"{OPENAI_PROJECT_API_KEY=}")
# logger.debug(f"{OPENAI_ASSISTANT_ID=}")
# logger.debug(f"{OPENAI_ORGANIZATION_ID=}")
# logger.debug(f"{AI_S3_ENDPOINT=}")
client = OpenAI(
    # api_key=os.environ.get("AI_ART_OPENAI_API_KEY", default=""),
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
)
# TODO: delete assistants that are not in openai cloud


def list_assistants(client: Client | None = None):
    if client is None:
        client = OpenAI(organization=OPENAI_ORGANIZATION_ID, project=OPENAI_PROJECT_ID)

    return client.beta.assistants.list()


def is_assistant_in_cloud(assistant_id: str) -> bool:
    assistants = list_assistants()
    return any(assistant.id == assistant_id for assistant in assistants)


def create_assistant() -> OpenAIAssistant:
    response = _create_assistant()
    return store_assistant(response)


def _create_assistant(client: Client | None = None) -> Assistant:
    if client is None:
        client = OpenAI(organization=OPENAI_ORGANIZATION_ID, project=OPENAI_PROJECT_ID)

    instructions = """        
        You are a articles writer on various topics. 
        You are writing in multiple languages (for example "en" as english, "es" as spanish, etc...)
        Output is structured jsonstring that can be parsed with JSON.parse. Output is minimalistic array (as you can see in output template).
        You will write title, perex, content, keywords, twitter post and prompt for DALL-E.
        Those keywords extract from content.
        Content split into multiple paragraphs. 
        Make article content approx 1000 words long.
        Create one langugage at once. 
        Do not give me information about what you are about to do. 
        Give me only output.
        Output json template:
        {
        "language":"{language code}",
       "title": "{title}",
        "perex":"{perex content}",
        "paragraphs":["{paragraphs of content in array}"],
        "keywords": ["{keywords in array}"],
        "image_prompt":"{prompt for DALL-E for create image based on this article}",
        "twitter":"{text for twitter post in english}"
        }
    
    """
    return client.beta.assistants.create(
        description="Assistant for the OpenAI-powered FastAPI app",
        name="OpenAI Assistant",
        model=OPENAI_GPT_MODEL,
        instructions=instructions,
    )


def store_assistant(assistant: Assistant) -> OpenAIAssistant:
    session = SessionLocal()
    new_assistant = OpenAIAssistant(
        assistant_id=assistant.id,
        instructions=assistant.instructions,
        model=assistant.model,
        description=assistant.description,
        name=assistant.name,
    )
    session.add(new_assistant)
    session.commit()
    return new_assistant


def get_most_recent_assistant(session: Session) -> OpenAIAssistant | None:
    return session.query(OpenAIAssistant).order_by(OpenAIAssistant.datetime_created.desc()).first()


def retrieve_assistant() -> str:
    session = SessionLocal()
    try:
        if session.query(OpenAIAssistant).count() == 0:
            return create_assistant().assistant_id
        assistant = get_most_recent_assistant(session)
        return assistant.assistant_id
    finally:
        session.close()


def handle_assistant():
    client = OpenAI(organization=OPENAI_ORGANIZATION_ID, project=OPENAI_PROJECT_ID)

    assistants = list_assistants(client=client)
    if len(assistants) == 0:
        create_assistant(client=client)


def command(topic: str):
    client = OpenAI(organization=OPENAI_ORGANIZATION_ID, project=OPENAI_PROJECT_ID)
    short_id = uuid.uuid4().hex[:8]
    message = f"Write a detailed, informative article about {topic}"

    threads = []

    # Create a single session to be used across all threads
    session = SessionLocal()
    try:
        for lang in ["czech", "english", "german"]:
            thread = threading.Thread(
                target=_generate, args=(message, client, short_id, lang, session)
            )
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Check if any threads raised exceptions
        for thread in threads:
            if hasattr(thread, "_exception"):
                logger.error(f"Thread failed with exception: {thread._exception}")
                raise thread._exception

        return short_id
    finally:
        session.close()


def _generate(
    message,
    client,
    short_id,
    lang: str,
    session: Session,
    max_retries: int = 3,
    retry_delay: int = 30,
):
    logger.info(f"generating in {lang}")

    for attempt in range(max_retries):
        try:
            thread = client.beta.threads.create()
            thread_id = thread.id

            # Get assistant_id within the retry loop
            assistant_id = retrieve_assistant()
            if not assistant_id:
                raise Exception("Failed to retrieve assistant ID")

            logger.info(f"Using assistant: {assistant_id}")

            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=f"{message} in language: {lang}",
            )

            run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

            while True:
                try:
                    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                except Exception as e:
                    logger.error(f"Error retrieving run: {e}")
                    break

                if run.status == "completed":
                    messages = client.beta.threads.messages.list(thread_id=thread_id)
                    for msg in messages:
                        save_to_database(short_id, msg, session)

                    try:
                        client.beta.threads.delete(thread_id=thread_id)
                        logger.info(f"Thread completed -> deleting thread {thread_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete thread {thread_id}: {e}")

                    return

                elif run.status == "failed":
                    logger.warning("Run failed, attempting one retry...")
                    try:
                        run = client.beta.threads.runs.create(
                            thread_id=thread_id, assistant_id=assistant_id
                        )
                        continue
                    except Exception as retry_error:
                        raise Exception(f"Run failed and retry failed: {retry_error}")
                elif run.status == "requires_action":
                    raise Exception("Run requires action - not implemented")

                time.sleep(5)

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for language {lang}: {str(e)}")
            if "Rate limit" in str(e) or "Thread limit" in str(e):
                if attempt < max_retries - 1:
                    logger.info(
                        f"Rate/Thread limit reached. Waiting {retry_delay} seconds before retry..."
                    )
                    time.sleep(retry_delay)
                    continue

            logger.error(f"Failed to generate content for {lang} after {attempt + 1} attempts")
            raise


def save_to_database(short_id: str, data: Message, session: Session):
    if data.role != "assistant":
        return

    try:
        content = data.content[0].text.value
        cleaned_str = content.strip()

        if cleaned_str.startswith("```json"):
            cleaned_str = cleaned_str[7:]
        if cleaned_str.endswith("```"):
            cleaned_str = cleaned_str[:-3]
        content = json.loads(cleaned_str)
        if content["language"] == "cz":
            content["language"] = "cs"
    except Exception as e:
        logger.error(f"invalid data: \n{data.content[0].text.value}")
        logger.error(e)
        return

    try:
        lang_id = session.query(Language).filter(Language.code == content["language"]).first().id
    except Exception as e:
        logger.error(content["language"])
        logger.error(e)
        return

    assistant_id = (
        session.query(OpenAIAssistant)
        .filter(OpenAIAssistant.assistant_id == data.assistant_id)
        .first()
        .id
    )

    article = Article(
        short_id=short_id,
        title=content["title"],
        perex=content["perex"],
        assistant_id=assistant_id,
        lang_id=lang_id,
        thread_id=data.thread_id,
        image_prompt=content["image_prompt"],
        twitter_text=content["twitter"],
    )
    session.add(article)
    session.commit()

    paragraphs = content["paragraphs"]
    logger.debug(f"article in {content['language']} added")

    for idx, paragraph in enumerate(paragraphs):
        session.add(Paragraph(content=paragraph, order=idx, article_id=article.id))

    session.commit()
    logger.debug("paragraphs added")

    keywords = content["keywords"]
    for keyword in keywords:
        try:
            session.add(Keyword(keyword=keyword, article_id=article.id, lang_id=lang_id))
            session.commit()
        except Exception:
            session.rollback()

    logger.debug("keywords added")

    if content["language"] == "en":
        generate_image(content["image_prompt"], client, short_id)


def generate_image(prompt, client, short_id="dummy_image"):
    if client is None:
        client = OpenAI(organization=OPENAI_ORGANIZATION_ID, project=OPENAI_PROJECT_ID)

    response = client.images.generate(model="dall-e-3", prompt=prompt, n=1, size="1024x1024")
    # The response includes URLs to the generated images
    image_url = response.data[0].url

    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        # Save the image to a file
        with open(f"{short_id}.png", "wb") as f:
            f.write(image_response.content)
        logger.info("Image successfully downloaded.")
        upload_file_to_s3(f"{short_id}.png")

    else:
        logger.info("Failed to download the image.")

    # upload_file_to_s3(f"{short_id}.png")


def upload_file_to_s3(file_name):
    """
    Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified, file_name is used
    :return: True if file was uploaded, else False
    """

    MIME_TYPE_MAPPING = {
        "webp": "image/webp",
        "jpg": "image/jpeg",
        "png": "image/png",
    }

    object_name = os.path.basename(file_name)

    try:
        session = boto3.session.Session()
        client = session.client(
            "s3",
            region_name=AI_S3_REGION,
            endpoint_url=f"https://{AI_S3_REGION}.digitaloceanspaces.com",
            aws_access_key_id=AI_S3_ACCESS_KEY,
            aws_secret_access_key=AI_S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )
    except Exception as e:
        logger.error(f"Error creating S3 client: {e}")
        return False

    try:
        extension = file_name.split(".")[-1]
        mimetype = MIME_TYPE_MAPPING.get(extension, "image")

        with open(file_name, "rb") as data:
            logger.debug(f"Uploading {file_name} to {AI_S3_BUCKET}/{object_name}")
            response = client.put_object(
                Bucket=AI_S3_BUCKET,
                Key=f"{AI_S3_IMAGE_FOLDER}/{object_name}",
                Body=data,
                ContentType=mimetype,
                ACL="public-read",
            )

        logger.info(response)
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            logger.info(f"File uploaded successfully to {AI_S3_BUCKET}/{object_name}")
            os.remove(file_name)

    except NoCredentialsError:
        logger.error("Credentials not available")
        return False
    except FileNotFoundError:
        logger.error("The file was not found")
        return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False

    return True
