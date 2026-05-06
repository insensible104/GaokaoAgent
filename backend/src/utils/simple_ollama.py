"""Custom Ollama wrapper using requests library directly"""
import requests
import json
from typing import Dict, List, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


class SimpleOllamaClient:
    """Simple ollama client using requests library"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b", temperature: float = 0.7):
        self.base_url = base_url
        self.model = model
        self.temperature = temperature

    def chat(self, messages: List[Dict], temperature: float = 0.7, format: str = None) -> str:
        """
        Send chat request to ollama

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Temperature parameter
            format: Optional format specification (e.g., 'json')

        Returns:
            Response content string
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        # Add format if specified (for JSON mode)
        if format:
            payload["format"] = format

        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        result = response.json()
        return result["message"]["content"]

    def invoke(self, prompt: str, temperature: float = None):
        """
        Simple invoke interface (compatible with langchain-style)

        Args:
            prompt: User prompt string
            temperature: Temperature parameter (uses instance default if None)

        Returns:
            Response object with 'content' attribute
        """
        if temperature is None:
            temperature = self.temperature

        messages = [{"role": "user", "content": prompt}]
        content = self.chat(messages, temperature)

        # Return object with content attribute for compatibility
        class Response:
            def __init__(self, content):
                self.content = content

        return Response(content)

    def with_structured_output(self, schema: Type[T]) -> 'StructuredOutputOllamaClient':
        """
        Return a client that enforces structured output according to the given Pydantic schema

        Args:
            schema: Pydantic BaseModel class defining the expected output structure

        Returns:
            StructuredOutputOllamaClient instance
        """
        return StructuredOutputOllamaClient(
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
            schema=schema
        )


class StructuredOutputOllamaClient:
    """Ollama client that enforces structured output using Pydantic schemas"""

    def __init__(self, base_url: str, model: str, temperature: float, schema: Type[BaseModel]):
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.schema = schema

    def invoke(self, prompt: str) -> BaseModel:
        """
        Invoke LLM with structured output enforcement

        Args:
            prompt: User prompt string

        Returns:
            Pydantic model instance matching the schema
        """
        # Add JSON schema instruction to prompt
        schema_json = self.schema.model_json_schema()

        enhanced_prompt = f"""{prompt}

请严格按照以下JSON格式返回结果，不要包含任何其他文字说明：

{json.dumps(schema_json, ensure_ascii=False, indent=2)}

只返回符合上述schema的JSON对象，不要有markdown格式包裹。"""

        # Call ollama with JSON format
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": enhanced_prompt}],
            "stream": False,
            "format": "json",  # Enable JSON mode
            "options": {
                "temperature": self.temperature
            }
        }

        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result["message"]["content"]

        # Parse JSON and validate against schema
        try:
            # Remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)
            return self.schema(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}\nResponse: {content}")
        except Exception as e:
            raise ValueError(f"Failed to validate response against schema: {e}\nResponse: {content}")
