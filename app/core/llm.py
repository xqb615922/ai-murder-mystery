"""AI 剧本杀 - LLM 客户端"""
from typing import Optional
from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.LLM_BASE_URL,
)


def chat(system_prompt: str, user_message: str, temperature: float = 0.7, model: Optional[str] = None) -> str:
    """简单对话接口"""
    model_name = model or settings.LLM_MODEL
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            extra_body={"enable_thinking": False},
        )
        return resp.choices[0].message.content
    except Exception as e:
        raise RuntimeError(
            f"LLM API 调用失败（{model_name}），"
            f"请检查 DASHSCOPE_API_KEY 是否有效。原始错误: {e}"
        )


def chat_json(system_prompt: str, user_message: str, temperature: float = 0.5, model: Optional[str] = None) -> str:
    """对话接口（低温度，输出更确定）"""
    return chat(system_prompt, user_message, temperature=temperature, model=model)
