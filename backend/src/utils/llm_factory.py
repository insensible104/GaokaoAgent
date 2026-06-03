"""统一的 LLM 工厂函数"""
import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 导入简单ollama客户端
from .simple_ollama import SimpleOllamaClient

# 确保加载 .env 文件
load_dotenv()


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

        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            timeout=120,
        )
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
