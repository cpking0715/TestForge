# TestForge AGENTS.md

## 一句话产品

自用/内部一站式测试平台：测试管理 + 接口/UI/APP 自动化 + AI 辅助 + CI。对标 ntesterc 类产品的功能逻辑（规格见 `docs/DEV-SPEC.md`），UI/文案全部自研。不做 SaaS/多租户/插件市场。

## 技术栈实例化

- 后端 `apps/server`：Python 3.13 + FastAPI + SQLAlchemy 2（同步）+ Alembic；测试 SQLite、开发/生产 PostgreSQL；JWT + 算术验证码
- 前端 `apps/web`：React 19 + Vite + TS + TailwindCSS；pnpm；API 调用只在 `src/features/*/api`；TS 类型从 OpenAPI 生成
- 部署 `deploy/`：docker-compose（postgres/redis）；nginx 反代 `/api` → server

## 常用命令（本仓库已验证）

```bash
# 后端（apps/server）
cd apps/server && uv sync
uv run pytest -q                      # 全部测试
uv run uvicorn tfserver.main:app --reload --port 8900   # 开发服（本机 8000 被其他服务占用，固定用 8900）

# 前端（apps/web）
cd apps/web && pnpm install
pnpm test                             # vitest
pnpm dev                              # 开发服（代理 /api → localhost:8900）

# 依赖服务
docker compose -f deploy/docker-compose.yml up -d
```

## 必测点（会翻车的切片）

- **验证码→登录闭环**：验证码 TTL 过期、答案错误、一次性消费、密码错误各自返回语义正确的 code/msg（契约测试锁定）
- **JWT 鉴权**：无 token/伪造 token/过期 token → 401 信封；RBAC 菜单接口未授权 → 拒绝
- **RBAC 数据完整性**：角色删菜单、用户绑角色、菜单树环路防护（parent 指向自己/后代）
- **响应信封**：所有 API 统一 `{code,msg,data}`，业务失败 code≠0，HTTP 状态与 code 解耦（契约测试 + 快照）

## 硬约束

- 分层 api→domain←infra：domain 不 import fastapi/sqlalchemy；外部能力走 `typing.Protocol` 端口 + FastAPI `Depends` 注入
- DTO / 领域实体 / 表模型三类分离，显式映射
- 行数红线：后端单文件 ≤300、路由文件 ≤200；前端组件 ≤150
- 凭据不落源码；`.env` 模板只放键名
- 后端模型不用 PG 专有列类型（测试要跑 SQLite）；需要 JSON 用 `sa.JSON`
- 用户可见文案中文；提交信息中文，走 `git_commit` 工具

## 侦查案卷

对标产品补充侦查走 reverse-skills case 案卷（`~/.agents/reverse-skills/work/testforge-recon/`），只读、授权范围内。
