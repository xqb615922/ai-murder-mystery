# AI 剧本杀 - 谁是凶手？

> AI 自动生成谋杀案剧本，玩家审问嫌疑人 Agent 推理凶手

## 技术栈

| 层 | 技术 | 用途 |
|---|---|---|
| Web | FastAPI | 后端 API |
| 前端 | Vue 3 + Tailwind CSS (CDN) | 游戏界面 |
| LLM | qwen3.6-plus（阿里百炼） | 剧本生成/Agent/评判 |
| 数据库 | PostgreSQL (Supabase) | 用户/游戏记录 |
| 缓存 | Redis (Upstash) | 会话/排行榜 |
| 向量库 | ChromaDB | 线索检索 |
| 部署 | Render.com | 公网访问 |

## 本地运行

```bash
pip install -r requirements.txt
python -m app.main
# 访问 http://localhost:8000
```

## 环境变量

```
DASHSCOPE_API_KEY=你的阿里百炼Key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```
