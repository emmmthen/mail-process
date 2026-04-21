# Application Package

`backend/app` 是后端应用包的入口，负责把 API、配置、数据模型和业务服务组装成可运行的 FastAPI 应用。

## 模块结构

- `main.py`：应用入口，注册中间件和路由
- `api/`：HTTP 路由层
- `core/`：配置、数据库等基础设施
- `models/`：ORM 模型
- `schemas/`：请求和响应结构
- `services/`：业务逻辑与流程编排

## 设计原则

- 入口层保持轻量
- 路由层薄，服务层厚
- Schema 与 ORM 分离
- 所有跨模块依赖通过明确接口传递

