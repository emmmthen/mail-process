# Backend

后端服务基于 `FastAPI` 构建，负责邮件导入、报价抽取、报价管理、系统设置和基础数据存储。

## 目录职责

- `app/`：应用主代码
- `data/`：本地开发数据与 SQLite 存储
- `pyproject.toml`：Python 项目配置
- `uv.lock`：依赖锁定文件

## 开发约定

- 路由层只负责请求和响应，不写复杂业务逻辑
- 业务逻辑放在 `app/services/`
- 数据结构分为 `models/` 和 `schemas/`
- 配置和数据库基础设施放在 `app/core/`

## 本地运行

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

也可以使用仓库脚本：

```bash
./scripts/start_backend.sh
```

## 主要接口

- `/api/quotes`：报价管理
- `/api/emails`：邮件处理
- `/api/settings`：系统设置
- `/health`：健康检查

