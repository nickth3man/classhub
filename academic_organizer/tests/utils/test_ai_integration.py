import pytest
from unittest.mock import patch, MagicMock
from academic_organizer.src.utils.ai_integration import OpenRouterClient, AIIntegrationError

@pytest.fixture
def mock_openrouter_response():
    return {
        "choices": [{
            "message": {
                "content": '{"topics": ["Python", "AI"], "complexity": 3}'
            }
        }]
    }

@pytest.fixture
def client():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        return OpenRouterClient()

def test_analyze_content_success(client, mock_openrouter_response):
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_openrouter_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        result = client.analyze_content("Test content")
        
        assert "topics" in result
        assert "complexity" in result
        mock_post.assert_called_once()

def test_analyze_content_api_error(client):
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException()
        
        with pytest.raises(AIIntegrationError):
            client.analyze_content("Test content")

def test_generate_study_materials(client, mock_openrouter_response):
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_openrouter_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        result = client.generate_study_materials("Test content", "flashcards")
        
        assert isinstance(result, dict)
        mock_post.assert_called_once()

def test_estimate_workload(client, mock_openrouter_response):
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_openrouter_response
        mock_post.return_value.raise_for_status = MagicMock()
        
        result = client.estimate_workload("Test assignment")
        
        assert isinstance(result, dict)
        mock_post.assert_called_once()