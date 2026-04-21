# Schemas

这里存放 Pydantic Schema，用于定义 API 请求和响应结构。

## 当前结构

- `email.py`：邮件导入、处理相关数据结构
- `quote.py`：报价相关请求和响应结构
- `settings.py`：系统设置相关结构

## 约定

- Schema 用于边界层输入输出，不直接替代 ORM
- 请求、响应、内部传输结构尽量分开
- 字段命名优先保持清晰和可读

