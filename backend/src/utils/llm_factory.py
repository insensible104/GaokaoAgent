"""统一的 LLM 工厂函数"""
import os
import json
import re
from typing import Any

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 导入简单ollama客户端
from .simple_ollama import SimpleOllamaClient

# 确保加载 .env 文件
load_dotenv()


class ManualStructuredOutputModel:
    """Provider-agnostic structured output via explicit JSON prompting."""

    def __init__(self, chat_model: ChatOpenAI, schema):
        self._chat_model = chat_model
        self._schema = schema

    @staticmethod
    def _extract_json(text: str) -> str:
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            return fenced.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]
        raise ValueError(f"Structured output did not contain a JSON object: {text[:200]}")

    def invoke(self, prompt: str, *args, **kwargs):
        schema_payload = self._schema.model_json_schema()
        structured_prompt = f"""{prompt}

Return ONLY one valid JSON object. Do not include markdown fences or extra text.
The JSON object must conform to this schema:
{json.dumps(schema_payload, ensure_ascii=False)}
"""
        response = self._chat_model.invoke(structured_prompt, *args, **kwargs)
        content = getattr(response, "content", response)
        payload = json.loads(self._extract_json(str(content)))
        return self._schema.model_validate(payload)


class DeepSeekChatOpenAI:
    """Small adapter for DeepSeek's OpenAI-compatible chat endpoint.

    DeepSeek-compatible models may reject OpenAI's `response_format` structured
    output path.  The project calls `with_structured_output(...)` in several
    agents, so use explicit JSON prompting for this provider.
    """

    def __init__(self, chat_model: ChatOpenAI):
        self._chat_model = chat_model

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat_model, name)

    def invoke(self, *args, **kwargs):
        return self._chat_model.invoke(*args, **kwargs)

    def with_structured_output(self, schema, **kwargs):
        return ManualStructuredOutputModel(self._chat_model, schema)

    def bind(self, *args, **kwargs):
        return DeepSeekChatOpenAI(self._chat_model.bind(*args, **kwargs))


def get_llm(temperature: float = 0.7):
    """
    获取 LLM 实例（统一工厂函数）

    Args:
        temperature: 温度参数

    Returns:
        LLM 实例（SimpleOllamaClient 或 ChatOpenAI）
    """
    provider = os.environ.get("LLM_PROVIDER", "cloud").strip().lower()

    print(f"[INFO] LLM Provider: {provider}")

    if provider == "local":
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

        print(f"[INFO] Using Local Ollama: {model} @ {base_url}")

        # Use simple ollama client (fixes 502 error with langchain-ollama)
        return SimpleOllamaClient(base_url=base_url, model=model, temperature=temperature)
    elif provider == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("AI_API_KEY")
        base_url = (
            os.environ.get("DEEPSEEK_BASE_URL")
            or os.environ.get("AI_BASE_URL")
            or "https://api.deepseek.com"
        )
        model = (
            os.environ.get("DEEPSEEK_MODEL")
            or os.environ.get("AI_MODEL")
            or "deepseek-chat"
        )

        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not set in .env file. "
                "Set DEEPSEEK_API_KEY or change LLM_PROVIDER to 'local'."
            )

        print(f"[INFO] Using DeepSeek: {model} @ {base_url}")

        return DeepSeekChatOpenAI(ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            timeout=120,
        ))
    else:
        api_key = os.environ.get("QWEN_API_KEY")
        base_url = os.environ.get("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = os.environ.get("QWEN_MODEL", "qwen-plus")

        if not api_key:
            raise ValueError(
                "QWEN_API_KEY not set in .env file. "
                "Either set QWEN_API_KEY or change LLM_PROVIDER to 'local'"
            )

        print(f"[INFO] Using Cloud Qwen: {model}")

        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            timeout=120  # 添加120秒超时，防止卡住
        )
