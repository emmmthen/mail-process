# Scripts

这里存放项目级脚本，主要用于本地启动、冒烟测试和数据处理。

## 当前脚本

- `start_backend.sh`：启动后端服务
- `start_frontend.sh`：启动前端开发服务
- `test-health-check.py`：健康检查
- `test-email-import.py`：邮件导入测试
- `test-email-processor.py`：邮件处理测试
- `test_data.py`：测试数据相关脚本
- `clean-test-data.py`：清理测试数据

## 使用约定

- 脚本应当可从仓库根目录直接执行
- 脚本只做自动化编排，不承载核心业务逻辑
- 测试脚本优先作为冒烟和回归验证工具

