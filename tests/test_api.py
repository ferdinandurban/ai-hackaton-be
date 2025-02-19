import pytest
from unittest.mock import patch  # Import for monkeypatching

from routers import openai_router 
from dependencies import get_db 


@pytest.mark.asyncio  # For testing async functions
async def test_generate_response(monkeypatch):
    # Set up a mock response
    mock_openai_response = {
        "choices": [{"text": "This is a mocked response from OpenAI."}]
    }

    # Patch the OpenAI Completion.create function
    monkeypatch.setattr(openai.Completion, "create", lambda **kwargs: mock_openai_response)

    # Simulate a database dependency for testing
    async def mocked_get_db():
        # You don't need a real database for this test
        pass

    app = openai_router.router 
    app.dependency_overrides[get_db] = mocked_get_db 

    # Create a testing client to simulate requests
    from fastapi.testclient import TestClient
    client = TestClient(app) 

    # Make a test request
    response = client.post("/generate", json={"prompt": "Test prompt"})

    # Assert the results
    assert response.status_code == 200
    assert response.json() == {"response": "This is a mocked response from OpenAI."}


@pytest.mark.asyncio
async def test_generate_response_api_error(monkeypatch):
    # Mock an OpenAI API error
    monkeypatch.setattr(
        openai.Completion, 
        "create", 
        lambda **kwargs: raise openai.error.APIError("Test API Error")
    )

    # ... (set up test similar to before)

    response = client.post("/generate", json={"prompt": "Test prompt"})

    assert response.status_code == 500
    assert response.json() == {"detail": "OpenAI API Error"}
