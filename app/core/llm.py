"""AI 剧本杀 - LLM 客户端"""
from openai import OpenAI
from app.core.config import settings

client = OpenAI(
    api_key=settings.DASHSCOPE_API_KEY,
    base_url=settings.LLM_BASE_URL,
)


def chat(system_prompt: str, user_message: str, temperature: float = 0.7) -> str:
    """简单对话接口"""
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        # qwen3.6-plus 启用思考模式时需要设置
        extra_body={"enable_thinking": False},
    )
    return resp.choices[0].message.content


def chat_json(system_prompt: str, user_message: str, temperature: float = 0.5) -> str:
    """对话接口（低温度，输出更确定）"""
    return chat(system_prompt, user_message, temperature=temperature)
