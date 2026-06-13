# AI 剧本杀 - 谁是凶手？

一个基于 AI 的剧本杀游戏，玩家通过审问嫌疑人、搜索线索来推理出凶手。

## 技术栈

- **后端**: FastAPI + SQLAlchemy + Redis
- **前端**: Vue 3 + Tailwind CSS (CDN)
- **AI**: 阿里百炼 qwen3.6-plus (Function Calling)
- **部署**: Render.com + Supabase + Upstash

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 启动
python -m uvicorn app.main:app --reload
```

访问 http://localhost:8000

## 游戏流程

1. 注册昵称进入游戏
2. 选择场景（或随机）
3. AI 生成剧本：4个嫌疑人 + 6条线索
4. 审问嫌疑人（每人最多5轮）
5. 搜索线索
6. 投票指认凶手
7. AI 裁判判定结果

## 云端部署

详见 `render.yaml`，支持一键部署到 Render.com。
