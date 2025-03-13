from typing import Dict, List, Optional, Union
import requests
from datetime import datetime
import json
import os
from functools import lru_cache

class AIIntegrationError(Exception):
    """Custom exception for AI integration errors"""
    pass

class OpenRouterClient:
    """Handles communication with OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise AIIntegrationError("OpenRouter API key not found in environment variables")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    @lru_cache(maxsize=100)
    def analyze_content(self, text: str) -> Dict:
        """Analyzes content for categorization and key information extraction"""
        prompt = self._build_analysis_prompt(text)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.default_headers,
                json={
                    "model": "anthropic/claude-2",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            return self._parse_analysis_response(response.json())
        except requests.exceptions.RequestException as e:
            raise AIIntegrationError(f"API request failed: {str(e)}")

    def generate_study_materials(self, content: str, material_type: str) -> Dict:
        """Generates study materials based on content"""
        prompt = self._build_study_prompt(content, material_type)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.default_headers,
                json={
                    "model": "anthropic/claude-2",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return self._parse_study_response(response.json())
        except requests.exceptions.RequestException as e:
            raise AIIntegrationError(f"Failed to generate study materials: {str(e)}")

    def estimate_workload(self, assignment_text: str) -> Dict:
        """Estimates workload and complexity for assignments"""
        prompt = self._build_workload_prompt(assignment_text)
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.default_headers,
                json={
                    "model": "anthropic/claude-2",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                }
            )
            response.raise_for_status()
            return self._parse_workload_response(response.json())
        except requests.exceptions.RequestException as e:
            raise AIIntegrationError(f"Workload estimation failed: {str(e)}")

    def _build_analysis_prompt(self, text: str) -> str:
        return f"""Analyze the following academic content and provide:
1. Main topics and subtopics
2. Key concepts
3. Suggested categories
4. Important dates or deadlines
5. Required actions or deliverables

Content:
{text}

Provide the analysis in JSON format."""

    def _build_study_prompt(self, content: str, material_type: str) -> str:
        prompts = {
            "flashcards": "Create a set of flashcards with questions and answers",
            "summary": "Provide a comprehensive summary with key points",
            "quiz": "Generate practice quiz questions with answers",
            "outline": "Create a structured outline of the content"
        }
        return f"""{prompts.get(material_type, "Analyze the content")} for:

{content}

Provide the response in JSON format."""

    def _build_workload_prompt(self, text: str) -> str:
        return f"""Analyze this assignment and estimate:
1. Time required (in hours)
2. Complexity level (1-5)
3. Required resources
4. Prerequisites
5. Suggested milestones

Assignment:
{text}

Provide the analysis in JSON format."""

    def _parse_analysis_response(self, response: Dict) -> Dict:
        try:
            content = response["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, json.JSONDecodeError) as e:
            raise AIIntegrationError(f"Failed to parse analysis response: {str(e)}")

    def _parse_study_response(self, response: Dict) -> Dict:
        try:
            content = response["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, json.JSONDecodeError) as e:
            raise AIIntegrationError(f"Failed to parse study materials response: {str(e)}")

    def _parse_workload_response(self, response: Dict) -> Dict:
        try:
            content = response["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, json.JSONDecodeError) as e:
            raise AIIntegrationError(f"Failed to parse workload response: {str(e)}")