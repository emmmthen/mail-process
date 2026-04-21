# Services

这里存放业务服务层，负责承接路由调用、组织数据流转、执行业务规则。

## 当前服务

- `email_processor.py`：邮件解析、内容提取和处理流程
- `quote_service.py`：报价管理逻辑
- `settings_service.py`：系统配置逻辑

## 设计原则

- 服务层承接业务主流程
- 不直接暴露 HTTP 细节
- 不把纯数据定义混进业务逻辑
- 复杂流程优先在这里收敛

