# TestForge

内部一站式测试平台：测试管理（ALM）+ 接口/UI/APP 自动化 + AI 辅助（用例生成、聊天助手、智能体）+ CI 集成。

> 新会话/新协作者请先读 [AGENTS.md](AGENTS.md)（协作约定与必测点）→ [docs/PRD.md](docs/PRD.md)（功能需求）→ [docs/ROADMAP.md](docs/ROADMAP.md)（施工路线与当前进度）。

## 快速开始

```bash
# 后端（默认 SQLite 零配置；生产/联调见下方切 PostgreSQL）
cd apps/server
uv sync
uv run uvicorn tfserver.main:app --reload --port 8900   # http://localhost:8900

# 前端
cd apps/web
pnpm install
pnpm dev                                                # http://localhost:5173（/api 代理到 8900）
```

首次启动自动建表并写入种子数据：账号 `admin` / `admin123`（超级管理员）。

## 测试（完成门禁）

```bash
cd apps/server && uv run pytest -q     # 后端：领域 + API 契约（SQLite 内存，零依赖）
cd apps/web && pnpm test               # 前端：vitest
cd apps/server && uv run python scripts/smoke_login.py   # 端到端登录冒烟（需后端在 8900 运行）
```

## 环境依赖（按阶段递增）

| 阶段 | 依赖 | 说明 |
|---|---|---|
| P0-P2（当前） | uv ≥0.12、Node ≥22 + pnpm ≥12 | 无其他必需项；Docker 可选 |
| 数据库升级 | Docker（PostgreSQL 16 + Redis 7） | `docker compose -f deploy/docker-compose.yml up -d`，然后配置 `.env`（参考 `.env.example`） |
| P3 AI 层 | 至少一个 LLM API Key | OpenAI 兼容协议（DeepSeek/DashScope/Ollama 均可） |
| P4 UI 自动化 | Playwright 浏览器 | `uv run playwright install chromium` |
| P5 APP 自动化 | Android SDK(adb)、模拟器/真机；抓包需 mitmproxy | 最重的一段，见 ROADMAP P5 |

## 目录结构

```
apps/server   FastAPI 后端（api / domain / infra 分层，src/tfserver）
apps/web      React 19 + Vite + TS + TailwindCSS 前端（features/ 组织）
deploy/       docker-compose（PostgreSQL / Redis）
docs/         PRD / DEV-SPEC / ROADMAP / ADR
```

## 约定速览

- 后端开发端口固定 **8900**（避开常见占用）；响应统一 `{code, msg, data}`
- 分层：api→domain←infra，domain 不 import 框架；行数红线：后端单文件 ≤300、路由 ≤200、前端组件 ≤150
- 凭据不落源码；`.env` 已被 gitignore，模板见 `.env.example`
- 内部使用，不做多租户/开放注册（完整边界见 PRD「明确不做」）
